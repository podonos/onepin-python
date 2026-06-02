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
