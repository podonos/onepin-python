"""``onepin skill install / path / uninstall`` -- manage the bundled cross-tool agent skill.

These commands materialize the OnePin agent skill (an open `Agent Skills <https://agentskills.io>`_
``SKILL.md`` folder bundled in the wheel) into each AI coding tool's skills directory, so the
skill is usable from Claude Code (as ``/onepin``), Cursor, OpenAI Codex, Gemini CLI, and Copilot.

They are pure local filesystem operations: no SDK import, no client, no authentication. That
keeps CLI startup fast (the fast-startup test forbids importing the SDK here) and lets the skill
be installed offline.
"""

from __future__ import annotations

import enum
import shutil
from pathlib import Path
from typing import Optional

import typer

from onepin._cli import _fsutil
from onepin._cli._ctx import CliError, _emit_error, output_json
from onepin._cli.auth.credentials import _home_path
from onepin._cli.render import render_json

# The bundled folder name. It becomes the slash command in tools that expose skills by name
# (Claude Code -> ``/onepin``), so it must stay ``onepin``.
_SKILL_NAME = "onepin"
_SKILL_PACKAGE = "onepin._cli._skill"


class _Tool(str, enum.Enum):
    """AI coding tools we can install the skill for."""

    claude = "claude"
    cursor = "cursor"
    codex = "codex"
    copilot = "copilot"
    gemini = "gemini"


# Per the verified Agent Skills install paths (vercel-labs/skills' Supported-Agents table):
# global (user) skills dirs are per-tool; in a project, Cursor/Codex/Copilot share ``.agents/skills``.
# ``detect`` is the tool's config root under HOME, used for auto-detection.
_TOOLS: dict[str, dict[str, str]] = {
    "claude": {"home": ".claude/skills", "project": ".claude/skills", "detect": ".claude"},
    "cursor": {"home": ".cursor/skills", "project": ".agents/skills", "detect": ".cursor"},
    "codex": {"home": ".codex/skills", "project": ".agents/skills", "detect": ".codex"},
    "copilot": {"home": ".copilot/skills", "project": ".agents/skills", "detect": ".copilot"},
    "gemini": {"home": ".gemini/skills", "project": ".gemini/skills", "detect": ".gemini"},
}


def install(
    tool: Optional[list[_Tool]] = typer.Option(
        None,
        "--tool",
        help="Target tool(s): claude, cursor, codex, copilot, gemini. Repeatable. Default: auto-detect.",
    ),
    all_tools: bool = typer.Option(False, "--all", help="Install for every supported tool."),
    project: bool = typer.Option(
        False, "--project", help="Install into the current project (./.claude, ./.agents, …) instead of HOME."
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite existing skill files."),
    json_output_local: bool = typer.Option(False, "--json", help="Emit JSON instead of text."),
) -> None:
    """Install the OnePin agent skill into your AI coding tool(s).

    Writes the bundled ``SKILL.md`` folder into each target's skills directory. In Claude Code the
    skill is then invocable as ``/onepin``; other tools load it on demand by relevance. Refuses to
    overwrite existing files unless ``--force`` is passed.
    """
    json_on = output_json(json_output_local)
    try:
        files = _bundled_skill_files()
        targets = _target_dirs(_select_tools(tool, all_tools), project)
        written: list[dict[str, object]] = []
        for labels, directory in targets:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise CliError("WRITE_FAILED", f"Could not create {directory}: {exc}") from exc
            for name, content in files:
                _write(directory / name, content, force=force)
            written.append({"tools": labels, "path": str(directory)})
    except CliError as exc:
        _emit_error(exc.code, exc.message, exc.request_id, json_on)
        raise typer.Exit(code=1) from exc

    if json_on:
        render_json({"ok": True, "command": "/onepin", "targets": written})
        return
    for labels, directory in targets:
        typer.echo(f"Installed OnePin skill → {directory}  ({', '.join(labels)})")
    typer.echo("In Claude Code, invoke it with /onepin; other tools load it by relevance.")
    typer.echo("If your tool is already running, restart it (or run /reload-plugins) to pick up a new skills dir.")


def path(
    tool: Optional[list[_Tool]] = typer.Option(None, "--tool", help="Target tool(s). Default: auto-detect."),
    all_tools: bool = typer.Option(False, "--all", help="Show paths for every supported tool."),
    project: bool = typer.Option(False, "--project", help="Show project paths instead of HOME."),
    json_output_local: bool = typer.Option(False, "--json", help="Emit JSON instead of text."),
) -> None:
    """Show where the OnePin skill is (or would be) installed, without writing anything."""
    json_on = output_json(json_output_local)
    try:
        targets = _target_dirs(_select_tools(tool, all_tools), project)
    except CliError as exc:
        _emit_error(exc.code, exc.message, exc.request_id, json_on)
        raise typer.Exit(code=1) from exc

    rows = [{"tools": labels, "path": str(d), "exists": d.exists()} for labels, d in targets]
    if json_on:
        render_json({"targets": rows})
        return
    for labels, directory in targets:
        state = "[installed]" if directory.exists() else "[not installed]"
        typer.echo(f"{directory}  ({', '.join(labels)})  {state}")


def uninstall(
    tool: Optional[list[_Tool]] = typer.Option(None, "--tool", help="Target tool(s). Default: auto-detect."),
    all_tools: bool = typer.Option(False, "--all", help="Uninstall from every supported tool."),
    project: bool = typer.Option(False, "--project", help="Uninstall from the current project instead of HOME."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the confirmation prompt."),
    json_output_local: bool = typer.Option(False, "--json", help="Emit JSON instead of text."),
) -> None:
    """Remove the installed OnePin skill folder(s). Idempotent; only deletes the ``onepin/`` leaf dir."""
    json_on = output_json(json_output_local)
    try:
        targets = _target_dirs(_select_tools(tool, all_tools), project)
        present = [(labels, d) for labels, d in targets if d.exists()]

        if present and not yes:
            if json_on:
                raise CliError(
                    "CONFIRMATION_REQUIRED",
                    "Pass --yes to remove the skill (no interactive prompt under --json).",
                )
            typer.confirm(f"Remove the OnePin skill from {len(present)} location(s)?", abort=True, err=True)

        removed: list[dict[str, object]] = []
        for labels, directory in present:
            _remove_skill_dir(directory)
            removed.append({"tools": labels, "path": str(directory)})
    except CliError as exc:
        _emit_error(exc.code, exc.message, exc.request_id, json_on)
        raise typer.Exit(code=1) from exc

    if json_on:
        render_json({"ok": True, "removed": removed})
        return
    if not removed:
        typer.echo("Nothing to remove.")
        return
    for entry in removed:
        typer.echo(f"Removed OnePin skill ← {entry['path']}")


# === helpers =============================================================================


def _select_tools(tools: Optional[list[_Tool]], all_tools: bool) -> list[str]:
    """Resolve which tools to act on: ``--all`` > explicit ``--tool`` > auto-detect > Claude.

    Auto-detection probes each tool's config root under HOME. If nothing is detected we fall back
    to Claude Code so the headline ``/onepin`` install always works.
    """
    if all_tools:
        return list(_TOOLS)
    if tools:
        seen: list[str] = []
        for t in tools:
            if t.value not in seen:
                seen.append(t.value)
        return seen
    home = _home_path()
    detected = [name for name, cfg in _TOOLS.items() if (home / cfg["detect"]).exists()]
    return detected or ["claude"]


def _target_dirs(tools: list[str], project: bool) -> list[tuple[list[str], Path]]:
    """Map tools to their ``…/onepin`` skill dirs, deduped by path (Cursor/Codex/Copilot share one in a project).

    Returns a list of ``(tools_sharing_this_dir, directory)`` preserving first-seen order.
    """
    base = Path.cwd() if project else _home_path()
    key = "project" if project else "home"
    by_path: dict[Path, list[str]] = {}
    order: list[Path] = []
    for name in tools:
        directory = base / _TOOLS[name][key] / _SKILL_NAME
        if directory not in by_path:
            by_path[directory] = []
            order.append(directory)
        by_path[directory].append(name)
    return [(by_path[directory], directory) for directory in order]


def _bundled_skill_files() -> list[tuple[str, bytes]]:
    """Read the bundled skill files (``SKILL.md`` + ``reference.md``) from package data."""
    from importlib import resources

    root = resources.files(_SKILL_PACKAGE).joinpath(_SKILL_NAME)
    files: list[tuple[str, bytes]] = []
    try:
        entries = sorted(root.iterdir(), key=lambda entry: entry.name)
    except (FileNotFoundError, NotADirectoryError) as exc:
        raise CliError("SKILL_PAYLOAD_MISSING", "The bundled OnePin skill is missing from the package.") from exc
    for entry in entries:
        if not entry.is_file() or entry.name.endswith(".py"):
            continue
        files.append((entry.name, entry.read_bytes()))
    if not files:
        raise CliError("SKILL_PAYLOAD_MISSING", "The bundled OnePin skill is missing from the package.")
    return files


def _write(dest: Path, content: bytes, *, force: bool) -> None:
    """Atomically write a skill file, mapping filesystem errors to stable CLI codes."""
    try:
        _fsutil.atomic_write_bytes(dest, content, force=force)
    except FileExistsError as exc:
        raise CliError("FILE_EXISTS", f"{dest} already exists. Pass --force to overwrite.") from exc
    except OSError as exc:
        raise CliError("WRITE_FAILED", f"Could not write {dest}: {exc}") from exc


def _remove_skill_dir(directory: Path) -> None:
    """Remove the ``onepin/`` skill leaf directory (never its parent ``skills/``)."""
    if directory.name != _SKILL_NAME:  # defensive: only ever delete our own leaf
        raise CliError("WRITE_FAILED", f"Refusing to remove unexpected path {directory}.")
    try:
        shutil.rmtree(directory)
    except OSError as exc:
        raise CliError("WRITE_FAILED", f"Could not remove {directory}: {exc}") from exc
