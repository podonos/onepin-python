"""``onepin schema`` -- the stable, machine-readable manifest of the whole CLI.

This is the agent contract (it supersedes parsing ``--help`` text, which is brittle). It is
built by introspecting the *assembled* Click command tree, so it covers table-driven
commands, hand-written composites, and auth uniformly -- whatever is wired into the app
shows up here.
"""

from __future__ import annotations

from typing import Any

import click
import typer

from onepin._cli.render import render_json


def build_manifest(app: typer.Typer) -> dict[str, Any]:
    """Introspect the assembled Typer app into a JSON-serializable manifest.

    Returns:
        ``{"name", "version", "commands": [ {group, name, args, options, destructive}, ... ]}``
        with one entry per leaf command, sorted by path for stable snapshots.
    """
    from onepin._cli import __version__

    cli = typer.main.get_command(app)
    commands: list[dict[str, Any]] = []
    _walk(cli, (), commands)
    commands.sort(key=lambda entry: entry["path"])
    return {"name": "onepin", "version": __version__, "commands": commands}


def _walk(command: Any, path: tuple[str, ...], out: list[dict[str, Any]]) -> None:
    """Recurse the Click command tree, appending a manifest entry per leaf command.

    Group detection is by capability (``list_commands``/``get_command``) rather than
    ``isinstance``: Typer's ``TyperGroup`` does not always satisfy ``isinstance(_, Group)``
    across click versions, so duck-typing is the robust check. The command/param objects
    are typed ``Any`` because they straddle the typer/click class boundary.
    """
    list_commands = getattr(command, "list_commands", None)
    get_command = getattr(command, "get_command", None)
    if callable(list_commands) and callable(get_command):
        ctx = _dummy_ctx(command)
        for name in list_commands(ctx):
            child = get_command(ctx, name)
            if child is None or getattr(child, "hidden", False):
                continue
            _walk(child, (*path, name), out)
        return
    out.append(_describe(command, path))


def _short_help(command: Any) -> str:
    """One-line help for a leaf command (the first line / summary of its docstring).

    Collapses internal whitespace so the rendered Markdown stays a single deterministic line.
    """
    text = command.get_short_help_str(limit=200) if hasattr(command, "get_short_help_str") else ""
    return " ".join(str(text).split())


def _dummy_ctx(command: Any) -> click.Context:
    return click.Context(command)


def _describe(command: Any, path: tuple[str, ...]) -> dict[str, Any]:
    """Describe a single leaf command (its args, options, destructiveness, output)."""
    args: list[dict[str, Any]] = []
    options: list[dict[str, Any]] = []
    destructive = False
    # ``param_type_name`` ("argument"/"option") is used instead of ``isinstance`` because
    # Typer's TyperArgument/TyperOption do not reliably satisfy isinstance against click's
    # Argument/Option across versions.
    for param in command.get_params(_dummy_ctx(command)):
        if param.param_type_name == "argument":
            args.append({"name": param.name})
        elif param.param_type_name == "option":
            flag = param.opts[0] if param.opts else (param.name or "")
            if "--yes" in param.opts or "-y" in param.opts:
                destructive = True
            if flag in ("-h", "--help"):
                continue
            options.append(
                {
                    "flag": flag,
                    "type": _option_type(param),
                    "required": bool(param.required),
                    "default": _safe_default(param.default),
                    "help": param.help or "",
                }
            )
    return {
        "path": list(path),
        "group": path[0] if path else "",
        "name": path[-1] if path else "",
        "args": args,
        "options": options,
        "destructive": destructive,
    }


def _option_type(param: Any) -> str:
    """Best-effort type name for an option (``choice`` enumerates allowed values)."""
    param_type = param.type
    choices = getattr(param_type, "choices", None)
    if choices is not None:
        return "choice[" + ",".join(str(c) for c in choices) + "]"
    if param.is_flag:
        return "bool"
    name = getattr(param_type, "name", None)
    return str(name) if name else "str"


def _safe_default(default: Any) -> Any:
    """Coerce a Click default to something JSON-serializable for the manifest."""
    if default is None or isinstance(default, (str, int, float, bool)):
        return default
    return str(default)


def schema(
    json_output_local: bool = typer.Option(False, "--json", help="Emit JSON (default for this command)."),
) -> None:
    """Print the machine-readable manifest of every CLI command (the agent contract)."""
    from onepin._cli.main import app

    render_json(build_manifest(app))


# === Deterministic Markdown command reference ============================================
# This renders the same command tree the manifest is built from (the single source of
# truth) into a stable Markdown inventory. ``scripts/gen_cli_docs.py`` splices the output
# into README between markers; ``tests/build/test_readme_in_sync.py`` fails CI on drift.
# No timestamps, no randomness -- identical output every run for a given command tree.


def _collect_leaves(command: Any, path: tuple[str, ...], out: list[dict[str, Any]]) -> None:
    """Recurse the assembled command tree, capturing ``path``/``help``/``args`` per leaf.

    Mirrors :func:`_walk` (same duck-typed group detection and hidden-command filtering) but
    additionally records each leaf's one-line help and positional arg names for rendering.
    """
    list_commands = getattr(command, "list_commands", None)
    get_command = getattr(command, "get_command", None)
    if callable(list_commands) and callable(get_command):
        ctx = _dummy_ctx(command)
        for name in list_commands(ctx):
            child = get_command(ctx, name)
            if child is None or getattr(child, "hidden", False):
                continue
            _collect_leaves(child, (*path, name), out)
        return
    args = [
        param.name
        for param in command.get_params(_dummy_ctx(command))
        if param.param_type_name == "argument" and param.name
    ]
    out.append({"path": list(path), "help": _short_help(command), "args": args})


def _command_line(entry: dict[str, Any]) -> str:
    """Render one command as a Markdown bullet: ``onepin <path> <ARGS>`` -- one-line help."""
    parts = ["onepin", *entry["path"], *(f"<{name}>" for name in entry["args"])]
    invocation = " ".join(parts)
    help_text = entry["help"]
    tail = f" — {help_text}" if help_text else ""
    return f"- `{invocation}`{tail}"


def render_markdown() -> str:
    """Render the assembled CLI command tree as a deterministic Markdown inventory.

    Builds from the same command tree the manifest introspects (``build_manifest``'s source
    of truth), groups by top-level group then subgroup, and emits a stable, sorted block.
    Contains no timestamps or randomness, so the output is byte-identical every run for a
    given command tree -- which lets a CI test gate the README against drift.

    Returns:
        The Markdown block (without surrounding markers), ending with a single newline.
    """
    from onepin._cli.main import app

    cli = typer.main.get_command(app)
    leaves: list[dict[str, Any]] = []
    _collect_leaves(cli, (), leaves)
    leaves.sort(key=lambda entry: entry["path"])

    # Bucket leaves by (group, subgroup). The group is the first path segment; the subgroup
    # is the middle segment for 3-deep paths (e.g. workflows runs list), else "".
    sections: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for entry in leaves:
        path = entry["path"]
        group = path[0] if path else ""
        subgroup = path[1] if len(path) >= 3 else ""
        sections.setdefault((group, subgroup), []).append(entry)

    lines: list[str] = ["## CLI command reference", ""]
    for group, subgroup in sorted(sections):
        heading = f"### {group}" if not subgroup else f"#### {group} {subgroup}"
        lines.append(heading)
        lines.append("")
        for entry in sections[(group, subgroup)]:
            lines.append(_command_line(entry))
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"
