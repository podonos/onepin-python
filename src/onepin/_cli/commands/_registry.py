"""Assemble the full command surface onto the root Typer app.

Wires:
- ``auth`` (login/logout/whoami) -- existing raw-httpx commands, untouched.
- Every table-driven command from :data:`onepin._cli._spec.TABLE`, grouped into sub-Typers
  (with nested sub-Typers for ``workflows runs`` and ``workspace members``/``stats``).
- Hand-written composites (``workflows run``, ``uploads create``, run downloads,
  ``workflows definition-schema``).
- The top-level ``schema`` manifest command.
"""

from __future__ import annotations

import typer

from onepin._cli import _dispatch, _manifest
from onepin._cli._spec import TABLE, Cmd
from onepin._cli.commands import auth, composites

# Per-group help text. Groups not listed fall back to a generic header.
_GROUP_HELP = {
    "workflows": "Create, run, and inspect workflows.",
    "templates": "Browse and manage gallery templates.",
    "voices": "Browse available voices.",
    "uploads": "Manage file uploads (presigned-S3 flow).",
    "workspace": "Manage workspaces, members, and statistics.",
    "usage": "Inspect workspace usage and activity.",
    "provider-keys": "Manage bring-your-own-key provider credentials.",
    "nodes": "Inspect available workflow node types.",
    "health": "API liveness and readiness probes.",
}

_SUBGROUP_HELP = {
    ("workflows", "runs"): "Inspect and control workflow runs.",
    ("workspace", "members"): "Manage workspace members and invites.",
    ("workspace", "stats"): "Workspace aggregate statistics.",
}


def register(app: typer.Typer) -> None:
    """Wire auth, all table-driven groups, composites, and the schema command onto ``app``."""
    # auth (unchanged raw-httpx path)
    app.command(name="login")(auth.login)
    app.command(name="logout")(auth.logout)
    app.command(name="whoami")(auth.whoami)

    groups = _build_groups()
    _wire_composites(groups)

    for name, group_app in groups.items():
        app.add_typer(group_app, name=name, help=_GROUP_HELP.get(name, f"Manage {name}."))

    app.command(name="schema", help="Emit the machine-readable JSON manifest of all commands.")(_manifest.schema)


def _build_groups() -> dict[str, typer.Typer]:
    """Build one sub-Typer per group, with nested sub-Typers for subgroups, from the TABLE."""
    groups: dict[str, typer.Typer] = {}
    subgroups: dict[tuple[str, str], typer.Typer] = {}

    for cmd in TABLE:
        group_app = groups.get(cmd.group)
        if group_app is None:
            group_app = typer.Typer(help=_GROUP_HELP.get(cmd.group, f"Manage {cmd.group}."), no_args_is_help=True)
            groups[cmd.group] = group_app

        target = group_app
        if cmd.subgroup:
            key = (cmd.group, cmd.subgroup)
            sub_app = subgroups.get(key)
            if sub_app is None:
                sub_app = typer.Typer(help=_SUBGROUP_HELP.get(key, f"Manage {cmd.subgroup}."), no_args_is_help=True)
                subgroups[key] = sub_app
                group_app.add_typer(sub_app, name=cmd.subgroup, help=_SUBGROUP_HELP.get(key))
            target = sub_app

        _dispatch.build(target, cmd)

    return groups


def _wire_composites(groups: dict[str, typer.Typer]) -> None:
    """Attach hand-written composites to their groups (creating groups if absent)."""
    workflows = groups.setdefault("workflows", typer.Typer(help=_GROUP_HELP["workflows"], no_args_is_help=True))
    uploads = groups.setdefault("uploads", typer.Typer(help=_GROUP_HELP["uploads"], no_args_is_help=True))

    workflows.command(name="run", help="Start a workflow run, optionally watching to completion.")(
        composites.workflow_run
    )
    workflows.command(name="definition-schema", help="Print the JSON Schema for a workflow definition.")(
        composites.definition_schema
    )

    runs = _find_subgroup(workflows, "runs")
    if runs is None:
        runs = typer.Typer(help=_SUBGROUP_HELP[("workflows", "runs")], no_args_is_help=True)
        workflows.add_typer(runs, name="runs")
    runs.command(name="download", help="Download a run's full export to a file.")(composites.run_download)
    runs.command(name="download-node", help="Download a single node's output to a file.")(composites.run_download_node)

    uploads.command(name="create", help="Upload a file via the presigned-S3 flow.")(composites.upload_create)


def _find_subgroup(parent: typer.Typer, name: str) -> typer.Typer | None:
    """Find an already-registered sub-Typer by name on a parent Typer."""
    for info in parent.registered_groups:
        if info.name == name and info.typer_instance is not None:
            return info.typer_instance
    return None


__all__ = ["register", "Cmd"]
