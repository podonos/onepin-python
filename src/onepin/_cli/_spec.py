"""Declarative command table: every table-driven CLI command described as data.

The CLI surface is ~55 near-identical commands over the Fern SDK. Rather than write a
function per command, each is a :class:`Cmd` row here and the dispatcher
(:mod:`onepin._cli._dispatch`) synthesizes a native Typer command from it. Hand-written
composites (``workflows run --watch``, ``uploads create``, downloads, schemas) live in
``commands/*`` and are wired separately.

Transforms, types, and unwrap modes are intentionally explicit strings/enums so the table
stays readable and the dispatcher stays a small interpreter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class Opt:
    """A single optional flag on a command.

    Attributes:
        flag: The CLI flag, e.g. ``--status`` (extra aliases space-separated, e.g. ``-l --limit``).
        type: One of ``"str"``, ``"int"``, ``"bool"``, ``"datetime"``, or a tuple of literal
            choices ``("a", "b", ...)`` which renders as a Typer Choice.
        default: Default value passed to ``typer.Option``.
        dest: SDK keyword the value is forwarded as (defaults to the flag name de-dashed).
        transform: Optional value transform applied before forwarding. One of
            ``"wrap_list"``, ``"comma_list"``, ``"datetime"``, ``"provider_key_request"``.
        help: Help text shown in ``--help`` and the JSON manifest.
        required: Whether Typer should require the flag.
        multiple: Whether the flag may be repeated (``list`` of values).
    """

    flag: str
    type: Any = "str"
    default: Any = None
    dest: Optional[str] = None
    transform: Optional[str] = None
    help: str = ""
    required: bool = False
    multiple: bool = False

    @property
    def dest_name(self) -> str:
        """The SDK keyword this option forwards as."""
        if self.dest is not None:
            return self.dest
        primary = self.flag.split()[0]
        return primary.lstrip("-").replace("-", "_")


@dataclass(frozen=True)
class Cmd:
    """A single table-driven command.

    Attributes:
        group: Top-level group name (``workflows``, ``templates``, ...).
        name: Command name within the group/subgroup.
        method: Dotted SDK method path relative to the client, e.g. ``workflows.list`` or
            ``workflows.runs.start``.
        help: Command help text.
        subgroup: Optional nested sub-Typer (``runs``, ``members``, ``stats``).
        args: Positional arguments, ``[(dest, help)]``; forwarded positionally in order.
        options: Optional flags.
        consts: Constant keyword arguments always injected (e.g. ``context_type="workflow"``).
        unwrap: Output mode -- ``"pager"``, ``"list"``, ``"data"``, or ``"action"``.
        columns: Column order for table rendering (``pager``/``list`` modes).
        success_msg: Message template for ``action``/``data`` modes (``{id}`` substituted).
        destructive: Whether the command mutates/deletes and requires ``--yes`` or confirm.
        redact: Whether the response contains fields in ``_SECRET_FIELDS`` that must be masked.
    """

    group: str
    name: str
    method: str
    help: str
    subgroup: Optional[str] = None
    args: list[tuple[str, str]] = field(default_factory=list)
    options: list[Opt] = field(default_factory=list)
    consts: dict[str, Any] = field(default_factory=dict)
    unwrap: str = "data"
    columns: list[str] = field(default_factory=list)
    success_msg: Optional[str] = None
    destructive: bool = False
    redact: bool = False

    @property
    def path(self) -> tuple[str, ...]:
        """The command path used by the manifest, e.g. ``("workflows", "runs", "list")``."""
        if self.subgroup:
            return (self.group, self.subgroup, self.name)
        return (self.group, self.name)


# --- Shared option fragments -------------------------------------------------------------

_LIMIT = Opt("--limit", "int", 50, help="Max rows to display (>=1).")
_JSON = Opt("--json", "bool", False, dest="json_output_local", help="Emit JSON instead of a table.")


def _list_opts(*extra: Opt) -> list[Opt]:
    return [_LIMIT, *extra, _JSON]


# Workflow run status filter / terminal states (SDK exposes run status as raw str; no enum).
_RUN_STATUS = ("draft", "running", "completed", "failed", "paused", "cancelled", "pending")

# Column presets keyed by output model.
_COLS_WORKFLOW = ["id", "name", "runs_count", "last_run_status", "updated_at"]
_COLS_VOICE = ["id", "name", "provider", "gender", "category"]
_COLS_TEMPLATE = ["id", "name", "category", "is_favorite", "uses_count"]
_COLS_RUN = ["id", "run_number", "status", "finished_steps", "total_steps", "created_at"]
_COLS_UPLOAD = ["id", "filename", "category", "status", "size_bytes"]
_COLS_MEMBER = ["id", "email", "role", "status", "last_active_at"]
_COLS_WORKSPACE = ["id", "name", "slug", "color_idx"]


# === The full command surface ============================================================
# Composites (workflows run/run --watch, uploads create, runs download/download-node,
# workflows definition-schema, schema) are hand-written in commands/* and NOT in this table.

TABLE: list[Cmd] = [
    # --- workflows ----------------------------------------------------------------------
    Cmd(
        "workflows",
        "list",
        "workflows.list",
        "List workflows in the workspace.",
        options=_list_opts(
            Opt("--status", _RUN_STATUS, None, help="Filter by workflow status."),
            Opt("--search", "str", None, help="Substring search over names."),
            Opt("--sort", ("name", "updated_at", "runs_count"), None, transform="wrap_list", help="Sort field."),
            Opt("--order", ("asc", "desc"), None, transform="wrap_list", help="Sort direction."),
        ),
        unwrap="pager",
        columns=_COLS_WORKFLOW,
    ),
    Cmd(
        "workflows",
        "show",
        "workflows.get",
        "Show a single workflow.",
        args=[("workflow_id", "Workflow UUID.")],
        options=[_JSON],
        unwrap="data",
    ),
    Cmd(
        "workflows",
        "create",
        "workflows.create_workflow",
        "Create a workflow.",
        options=[
            Opt("--name", "str", None, required=True, help="Workflow name."),
            Opt("--description", "str", None, help="Workflow description."),
            Opt(
                "--definition",
                "str",
                None,
                dest="definition",
                transform="json_file",
                help="Workflow definition: inline JSON or @path/to/file.json. "
                "Recipe: `nodes list` -> `nodes show <type>` -> `workflows definition-schema`, "
                "or copy `.definition` from `templates show`/`workflows show`.",
            ),
            _JSON,
        ],
        unwrap="data",
        success_msg="Created workflow {id}.",
    ),
    Cmd(
        "workflows",
        "update",
        "workflows.patch_workflow",
        "Update a workflow (partial patch).",
        args=[("workflow_id", "Workflow UUID.")],
        options=[
            Opt("--name", "str", None, help="New name."),
            Opt("--description", "str", None, help="New description."),
            Opt(
                "--definition",
                "str",
                None,
                dest="definition",
                transform="json_file",
                help="New definition: inline JSON or @path/to/file.json.",
            ),
            _JSON,
        ],
        unwrap="data",
        success_msg="Updated workflow {id}.",
    ),
    Cmd(
        "workflows",
        "delete",
        "workflows.delete_workflow",
        "Delete a workflow.",
        args=[("workflow_id", "Workflow UUID.")],
        options=[_JSON],
        unwrap="action",
        success_msg="Deleted workflow {workflow_id}.",
        destructive=True,
    ),
    Cmd(
        "workflows",
        "duplicate",
        "workflows.duplicate_workflow",
        "Duplicate a workflow.",
        args=[("workflow_id", "Workflow UUID.")],
        options=[_JSON],
        unwrap="data",
        success_msg="Duplicated workflow into {id}.",
    ),
    Cmd(
        "workflows",
        "uploads",
        "workflows.list_workflow_uploads",
        "List a workflow's uploads.",
        args=[("workflow_id", "Workflow UUID.")],
        options=[_JSON],
        unwrap="list",
        columns=_COLS_UPLOAD,
    ),
    Cmd(
        "workflows",
        "preview-run",
        "workflows.preview_run",
        "Estimate cost of a run without executing.",
        args=[("workflow_id", "Workflow UUID.")],
        options=[_JSON],
        unwrap="data",
    ),
    # --- workflows runs (subgroup) ------------------------------------------------------
    Cmd(
        "workflows",
        "list",
        "workflows.runs.list",
        "List runs for a workflow.",
        subgroup="runs",
        args=[("workflow_id", "Workflow UUID.")],
        options=_list_opts(
            Opt("--status", _RUN_STATUS, None, help="Filter by run status."),
            Opt("--search", "str", None, help="Substring search."),
            Opt("--sort", ("created_at", "started_at", "completed_at", "status"), None, help="Sort field."),
            Opt("--order", ("asc", "desc"), None, help="Sort direction."),
        ),
        unwrap="pager",
        columns=_COLS_RUN,
    ),
    Cmd(
        "workflows",
        "show",
        "workflows.runs.get",
        "Show a single run.",
        subgroup="runs",
        args=[("workflow_id", "Workflow UUID."), ("run_id", "Run UUID.")],
        options=[_JSON],
        unwrap="data",
    ),
    Cmd(
        "workflows",
        "status",
        "workflows.runs.status",
        "Show a run's current status.",
        subgroup="runs",
        args=[("workflow_id", "Workflow UUID."), ("run_id", "Run UUID.")],
        options=[_JSON],
        unwrap="data",
    ),
    Cmd(
        "workflows",
        "cancel",
        "workflows.runs.cancel",
        "Cancel a running run.",
        subgroup="runs",
        args=[("workflow_id", "Workflow UUID."), ("run_id", "Run UUID.")],
        options=[_JSON],
        unwrap="data",
        success_msg="Cancelled run {id}.",
        destructive=True,
    ),
    Cmd(
        "workflows",
        "steps",
        "workflows.get_run_steps",
        "List the steps of a run.",
        subgroup="runs",
        args=[("workflow_id", "Workflow UUID."), ("run_id", "Run UUID.")],
        options=[_JSON],
        unwrap="list",
        columns=[],
    ),
    Cmd(
        "workflows",
        "overview",
        "workflows.get_run_overview",
        "Show a run's node overview.",
        subgroup="runs",
        args=[("workflow_id", "Workflow UUID."), ("run_id", "Run UUID.")],
        options=[_JSON],
        unwrap="data",
    ),
    Cmd(
        "workflows",
        "data",
        "workflows.get_run_data",
        "Show a run's output data.",
        subgroup="runs",
        args=[("workflow_id", "Workflow UUID."), ("run_id", "Run UUID.")],
        options=[
            Opt("--search", "str", None, help="Substring search over output rows."),
            Opt("--language", "str", None, help="Filter by language."),
            Opt("--limit", "int", None, help="Max rows."),
            Opt("--offset", "int", None, help="Row offset."),
            _JSON,
        ],
        unwrap="data",
    ),
    Cmd(
        "workflows",
        "summary",
        "workflows.runs_summary",
        "Summarize a workflow's runs.",
        subgroup="runs",
        args=[("workflow_id", "Workflow UUID.")],
        options=[
            Opt("--from", "datetime", None, dest="from_", transform="datetime", help="Start of window (ISO 8601)."),
            Opt("--to", "datetime", None, dest="to", transform="datetime", help="End of window (ISO 8601)."),
            _JSON,
        ],
        unwrap="data",
    ),
    # --- templates ----------------------------------------------------------------------
    Cmd(
        "templates",
        "list",
        "templates.list",
        "List gallery templates.",
        options=_list_opts(
            Opt(
                "--category",
                ("media", "creative", "business", "education", "wellness"),
                None,
                transform="wrap_list",
                help="Filter by category.",
            ),
            Opt("--search", "str", None, help="Substring search."),
            Opt("--sort", ("popular", "recent", "name"), None, help="Sort order."),
            Opt("--favorites-only", "bool", False, help="Only favorited templates."),
        ),
        unwrap="pager",
        columns=_COLS_TEMPLATE,
    ),
    Cmd(
        "templates",
        "show",
        "templates.get",
        "Show a single template.",
        args=[("template_id", "Template UUID.")],
        options=[_JSON],
        unwrap="data",
    ),
    Cmd(
        "templates",
        "create",
        "templates.create_template",
        "Create a template.",
        options=[
            Opt("--name", "str", None, required=True, help="Template name."),
            Opt("--description", "str", None, help="Template description."),
            Opt(
                "--category",
                ("media", "creative", "business", "education", "wellness"),
                None,
                help="Template category.",
            ),
            Opt(
                "--definition",
                "str",
                None,
                dest="definition",
                transform="json_file",
                help="Definition: inline JSON or @path/to/file.json.",
            ),
            _JSON,
        ],
        unwrap="data",
        success_msg="Created template {id}.",
    ),
    Cmd(
        "templates",
        "update",
        "templates.update_template",
        "Update a template.",
        args=[("template_id", "Template UUID.")],
        options=[
            Opt("--name", "str", None, help="New name."),
            Opt("--description", "str", None, help="New description."),
            Opt("--category", ("media", "creative", "business", "education", "wellness"), None, help="New category."),
            Opt(
                "--definition",
                "str",
                None,
                dest="definition",
                transform="json_file",
                help="New definition: inline JSON or @path/to/file.json.",
            ),
            _JSON,
        ],
        unwrap="data",
        success_msg="Updated template {id}.",
    ),
    Cmd(
        "templates",
        "delete",
        "templates.delete_template",
        "Delete a template.",
        args=[("template_id", "Template UUID.")],
        options=[_JSON],
        unwrap="action",
        success_msg="Deleted template {template_id}.",
        destructive=True,
    ),
    Cmd(
        "templates",
        "clone",
        "templates.clone",
        "Clone a template into a new workflow.",
        args=[("template_id", "Template UUID.")],
        options=[Opt("--name", "str", None, help="Name for the new workflow."), _JSON],
        unwrap="data",
        success_msg="Cloned template into workflow {id}.",
    ),
    Cmd(
        "templates",
        "favorite",
        "templates.favorite_template",
        "Favorite a template.",
        args=[("template_id", "Template UUID.")],
        options=[_JSON],
        unwrap="data",
        success_msg="Favorited template {id}.",
    ),
    Cmd(
        "templates",
        "unfavorite",
        "templates.unfavorite_template",
        "Unfavorite a template.",
        args=[("template_id", "Template UUID.")],
        options=[_JSON],
        unwrap="action",
        success_msg="Unfavorited template {template_id}.",
    ),
    # --- voices -------------------------------------------------------------------------
    Cmd(
        "voices",
        "list",
        "voices.list",
        "List available voices.",
        options=_list_opts(
            Opt("--favorites-only", "bool", False, help="Only favorited voices."),
            Opt("--gender", ("male", "female", "neutral"), None, transform="wrap_list", help="Filter by gender."),
            Opt(
                "--provider",
                ("cartesia", "elevenlabs", "naver", "respeecher", "rime"),
                None,
                transform="wrap_list",
                help="Filter by provider.",
            ),
            Opt(
                "--language",
                "str",
                None,
                transform="comma_list",
                multiple=False,
                help="Filter by language code(s), comma-separated (e.g. en-us,ko-kr).",
            ),
            Opt("--search", "str", None, help="Substring search."),
        ),
        unwrap="pager",
        columns=_COLS_VOICE,
    ),
    Cmd(
        "voices",
        "show",
        "voices.get",
        "Show a single voice.",
        args=[("voice_id", "Voice UUID.")],
        options=[_JSON],
        unwrap="data",
    ),
    Cmd(
        "voices",
        "similar",
        "voices.similar",
        "List voices similar to a voice.",
        args=[("voice_id", "Voice UUID.")],
        options=[
            Opt("--limit", "int", None, help="Max results."),
            Opt("--language", "str", None, transform="comma_list", help="Language code(s), comma-separated."),
            _JSON,
        ],
        unwrap="list",
        columns=_COLS_VOICE,
    ),
    Cmd(
        "voices",
        "favorite",
        "voices.favorite_voice",
        "Favorite a voice.",
        args=[("voice_id", "Voice UUID.")],
        options=[_JSON],
        unwrap="data",
        success_msg="Favorited voice {id}.",
    ),
    Cmd(
        "voices",
        "unfavorite",
        "voices.unfavorite_voice",
        "Unfavorite a voice.",
        args=[("voice_id", "Voice UUID.")],
        options=[_JSON],
        unwrap="action",
        success_msg="Unfavorited voice {voice_id}.",
    ),
    # --- uploads (confirm/delete; create is a composite) --------------------------------
    Cmd(
        "uploads",
        "confirm",
        "uploads.confirm",
        "Confirm an upload and attach it to a workflow.",
        args=[("upload_id", "Upload UUID.")],
        options=[
            Opt(
                "--workflow-id",
                "str",
                None,
                dest="context_id",
                required=True,
                help="Workflow UUID to attach the upload to.",
            ),
            _JSON,
        ],
        consts={"context_type": "workflow"},
        unwrap="data",
        success_msg="Confirmed upload {id}.",
    ),
    Cmd(
        "uploads",
        "delete",
        "uploads.delete",
        "Delete an upload.",
        args=[("upload_id", "Upload UUID.")],
        options=[_JSON],
        unwrap="action",
        success_msg="Deleted upload {upload_id}.",
        destructive=True,
    ),
    # --- workspace ----------------------------------------------------------------------
    Cmd(
        "workspace",
        "list",
        "workspaces.list_workspaces",
        "List workspaces.",
        options=_list_opts(),
        unwrap="list",
        columns=_COLS_WORKSPACE,
    ),
    Cmd(
        "workspace",
        "create",
        "workspaces.create_workspace",
        "Create a workspace.",
        options=[
            Opt("--name", "str", None, required=True, help="Workspace name."),
            Opt("--slug", "str", None, help="URL slug."),
            Opt("--color-idx", "int", None, dest="color_idx", help="Color index."),
            _JSON,
        ],
        unwrap="data",
        success_msg="Created workspace {id}.",
    ),
    Cmd(
        "workspace",
        "show",
        "workspaces.get_workspace",
        "Show a workspace.",
        args=[("workspace_id", "Workspace UUID.")],
        options=[_JSON],
        unwrap="data",
    ),
    Cmd(
        "workspace",
        "update",
        "workspaces.update_workspace",
        "Update a workspace.",
        args=[("workspace_id", "Workspace UUID.")],
        options=[
            Opt("--name", "str", None, help="New name."),
            Opt("--slug", "str", None, help="New slug."),
            Opt("--color-idx", "int", None, dest="color_idx", help="New color index."),
            _JSON,
        ],
        unwrap="data",
        success_msg="Updated workspace {id}.",
    ),
    Cmd(
        "workspace",
        "delete",
        "workspaces.delete_workspace",
        "Delete a workspace.",
        args=[("workspace_id", "Workspace UUID.")],
        options=[_JSON],
        unwrap="action",
        success_msg="Deleted workspace {workspace_id}.",
        destructive=True,
    ),
    Cmd(
        "workspace",
        "settings",
        "workspace.get_workspace_settings",
        "Show a workspace's settings.",
        args=[("ws_id", "Workspace UUID.")],
        options=[_JSON],
        unwrap="data",
    ),
    # --- workspace members (subgroup) ---------------------------------------------------
    Cmd(
        "workspace",
        "list",
        "workspace_members.list_members",
        "List workspace members.",
        subgroup="members",
        args=[("ws_id", "Workspace UUID.")],
        options=[_JSON],
        unwrap="list",
        columns=_COLS_MEMBER,
    ),
    Cmd(
        "workspace",
        "invite",
        "workspace_members.create_invite",
        "Invite a member.",
        subgroup="members",
        args=[("ws_id", "Workspace UUID.")],
        options=[
            Opt("--email", "str", None, required=True, help="Invitee email."),
            Opt("--role", ("admin", "editor", "viewer"), None, required=True, help="Role to grant."),
            _JSON,
        ],
        unwrap="data",
        success_msg="Invited {email}.",
    ),
    Cmd(
        "workspace",
        "remove",
        "workspace_members.remove_member",
        "Remove a member.",
        subgroup="members",
        args=[("ws_id", "Workspace UUID."), ("member_id", "Member UUID.")],
        options=[_JSON],
        unwrap="action",
        success_msg="Removed member {member_id}.",
        destructive=True,
    ),
    Cmd(
        "workspace",
        "set-role",
        "workspace_members.update_member_role",
        "Change a member's role.",
        subgroup="members",
        args=[("ws_id", "Workspace UUID."), ("member_id", "Member UUID.")],
        options=[Opt("--role", ("admin", "editor", "viewer"), None, required=True, help="New role."), _JSON],
        unwrap="action",
        success_msg="Updated role for member {member_id}.",
    ),
    Cmd(
        "workspace",
        "revoke-invite",
        "workspace_members.revoke_invite",
        "Revoke a pending invite.",
        subgroup="members",
        args=[("ws_id", "Workspace UUID."), ("invite_id", "Invite UUID.")],
        options=[_JSON],
        unwrap="action",
        success_msg="Revoked invite {invite_id}.",
        destructive=True,
    ),
    Cmd(
        "workspace",
        "invite-role",
        "workspace_members.update_invite_role",
        "Change a pending invite's role.",
        subgroup="members",
        args=[("ws_id", "Workspace UUID."), ("invite_id", "Invite UUID.")],
        options=[Opt("--role", ("admin", "editor", "viewer"), None, required=True, help="New role."), _JSON],
        unwrap="data",
        success_msg="Updated invite {id}.",
    ),
    Cmd(
        "workspace",
        "accept",
        "workspace_members.accept_invite",
        "Accept an invite by token.",
        subgroup="members",
        args=[("token", "Invite token.")],
        options=[_JSON],
        unwrap="action",
        success_msg="Accepted invite.",
    ),
    # --- usage --------------------------------------------------------------------------
    Cmd(
        "usage",
        "summary",
        "usage.usage_summary",
        "Usage summary.",
        options=[
            Opt("--range", ("30d", "60d", "90d"), None, help="Time range."),
            Opt(
                "--activity-view",
                ("daily", "weekly", "monthly"),
                None,
                dest="activity_view",
                help="Aggregation granularity.",
            ),
            Opt("--timezone", "str", None, help="IANA timezone."),
            _JSON,
        ],
        unwrap="data",
    ),
    Cmd(
        "usage",
        "by-language",
        "usage.usage_by_language",
        "Usage broken down by language.",
        options=[
            Opt("--range", ("30d", "60d", "90d"), None, help="Time range."),
            Opt(
                "--activity-view",
                ("daily", "weekly", "monthly"),
                None,
                dest="activity_view",
                help="Aggregation granularity.",
            ),
            Opt("--timezone", "str", None, help="IANA timezone."),
            _JSON,
        ],
        unwrap="data",
    ),
    Cmd(
        "usage",
        "activity",
        "usage.usage_activity",
        "Recent workspace activity.",
        options=[
            Opt("--range", ("30d", "60d", "90d"), None, help="Time range."),
            Opt(
                "--type",
                (
                    "workflow_run",
                    "voice_generated",
                    "template_applied",
                    "member_invited",
                    "api_key_created",
                    "settings_changed",
                ),
                None,
                help="Activity type filter.",
            ),
            Opt("--user-id", "str", None, dest="user_id", help="Filter by user UUID."),
            Opt("--limit", "int", None, help="Max rows."),
            Opt("--cursor", "str", None, help="Pagination cursor."),
            Opt("--timezone", "str", None, help="IANA timezone."),
            _JSON,
        ],
        unwrap="list",
        columns=[],
    ),
    # --- nodes --------------------------------------------------------------------------
    Cmd(
        "nodes",
        "list",
        "nodes.list_nodes",
        "List available node types.",
        options=[_JSON],
        unwrap="list",
        columns=[],
    ),
    Cmd(
        "nodes",
        "show",
        "nodes.get_node_detail",
        "Show a node type's detail (runtime options).",
        args=[("node_type", "Node type identifier.")],
        options=[_JSON],
        unwrap="data",
    ),
]
