"""Table-driven dispatcher: synthesize native Typer commands from :data:`onepin._cli._spec.TABLE`.

For each :class:`~onepin._cli._spec.Cmd` row, :func:`build` creates a real function whose
``inspect.Signature`` + ``__annotations__`` are synthesized so Typer parses args/options,
renders ``--help``, and reports parameter sources exactly as for a hand-written command (no
``makefun``, no Click-in-Typer). The function body lazy-imports the SDK context, resolves a
client, applies declared transforms, conditionally forwards ``workspace_id``, calls the SDK
method under the error-mapping context manager, and emits via the row's unwrap mode.
"""

from __future__ import annotations

import enum
import inspect
import json
from itertools import islice
from typing import Any, Callable, Optional

import typer

from onepin._cli import _state
from onepin._cli._ctx import CliError, api_errors, get_client, output_json, to_jsonable
from onepin._cli._spec import Cmd, Opt
from onepin._cli.render import render_json, render_table

# Run statuses that the SDK reports as terminal. Used by composites; kept here so the
# constant lives next to the dispatcher that knows the run-status string contract.
TERMINAL_RUN_STATES = frozenset({"completed", "failed", "cancelled"})

# Cache for synthesized Choice enums so identical literal tuples reuse one type.
_ENUM_CACHE: dict[tuple[str, ...], type[enum.Enum]] = {}


def _choice_enum(name: str, choices: tuple[str, ...]) -> type[enum.Enum]:
    """Build (and cache) a str Enum so Typer renders a Choice for a literal-tuple option."""
    if choices in _ENUM_CACHE:
        return _ENUM_CACHE[choices]
    members = {value.replace("-", "_").replace(".", "_").upper(): value for value in choices}
    created = enum.Enum(name, members, type=str)  # type: ignore[misc]
    _ENUM_CACHE[choices] = created
    return created


def _annotation_for(opt: Opt) -> Any:
    """Map an Opt's declared type to a Python annotation Typer understands."""
    if isinstance(opt.type, tuple):
        ident = "Choice_" + "_".join(opt.type)
        return Optional[_choice_enum(ident, opt.type)]
    if opt.type == "int":
        return Optional[int]
    if opt.type == "bool":
        return bool
    if opt.type == "datetime":
        return Optional[str]
    return Optional[str]


def _resolve_method(client: Any, paths: str | tuple[str, ...]) -> Callable[..., Any]:
    """Resolve the first available dotted SDK method path against a built client."""
    candidates = (paths,) if isinstance(paths, str) else paths
    last_error: AttributeError | None = None
    for dotted in candidates:
        obj: Any = client
        try:
            for part in dotted.split("."):
                obj = getattr(obj, part)
        except AttributeError as exc:
            last_error = exc
            continue
        return obj  # type: ignore[no-any-return]

    attempted = ", ".join(repr(path) for path in candidates)
    raise AttributeError(f"Could not resolve SDK method; attempted paths: {attempted}") from last_error


def _coerce_value(value: Any) -> Any:
    """Unwrap an Enum member to its value (Typer passes Enum instances for Choice options)."""
    if isinstance(value, enum.Enum):
        return value.value
    return value


def _apply_transform(opt: Opt, value: Any) -> Any:
    """Apply an option's declared transform to a parsed value (None passes through)."""
    if value is None:
        return None
    value = _coerce_value(value)
    transform = opt.transform
    if transform is None:
        return value
    if transform == "wrap_list":
        return [value]
    if transform == "comma_list":
        return [piece.strip() for piece in str(value).split(",") if piece.strip()]
    if transform == "datetime":
        return _parse_datetime(value)
    if transform == "provider_key_request":
        return _provider_key_request(value)
    if transform == "json_file":
        return value  # handled separately (needs the target pydantic model)
    raise CliError("INTERNAL", f"Unknown transform {transform!r}")


def _parse_datetime(value: str) -> Any:
    """Parse an ISO-8601 string to a datetime (accepts a trailing ``Z``)."""
    import datetime as dt

    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return dt.datetime.fromisoformat(text)
    except ValueError as exc:
        raise CliError("INVALID_DATETIME", f"Could not parse datetime {value!r}: {exc}") from exc


def _provider_key_request(value: str) -> dict[str, Any]:
    """Coerce a ``--key`` value into the provider credential payload dict.

    Accepts inline JSON (``{"api_key": "..."}``) or a bare key string (wrapped as
    ``{"api_key": value}``). Never logged or echoed -- the secret stays in the request body.
    """
    text = str(value).strip()
    if text.startswith("{"):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise CliError("INVALID_JSON", f"--key looks like JSON but did not parse: {exc}") from exc
        if not isinstance(parsed, dict):
            raise CliError("INVALID_KEY", "--key JSON must be an object.")
        return parsed
    return {"api_key": text}


def _load_definition(raw: str) -> Any:
    """Load a workflow/template definition (inline JSON or ``@path``) into the SDK input model.

    Constructs and validates ``WorkflowDefinitionInput`` so a bad shape surfaces as a clean
    ``VALIDATION_ERROR`` (caught by the error mapper) rather than a server round-trip.
    """
    text = raw.strip()
    if text.startswith("@"):
        path = text[1:]
        # FileNotFoundError / PermissionError / IsADirectoryError are mapped by api_errors().
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    payload = json.loads(text)
    from onepin.types import WorkflowDefinitionInput

    return WorkflowDefinitionInput.model_validate(payload)


def _accepts_workspace_kwarg(method: Callable[..., Any]) -> bool:
    """Return True if ``method`` takes ``workspace_id`` as the *scoping* keyword.

    The SDK's workspace-scoping kwarg is always keyword-only (declared after ``*``). A
    method whose path parameter happens to be named ``workspace_id`` (e.g.
    ``workspaces.get_workspace(workspace_id, *, ...)``) exposes it as POSITIONAL_OR_KEYWORD,
    not keyword-only -- forwarding the root ``--workspace`` there would collide with the
    positional path argument. So we require ``KEYWORD_ONLY`` specifically.
    """
    try:
        params = inspect.signature(method).parameters
    except (TypeError, ValueError):
        return False
    param = params.get("workspace_id")
    if param is None:
        # Tolerate **kwargs-only fakes in tests, but never for a positional collision.
        return any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    return param.kind == inspect.Parameter.KEYWORD_ONLY


def _build_kwargs(cmd: Cmd, bound: dict[str, Any]) -> tuple[list[Any], dict[str, Any]]:
    """Split the bound CLI arguments into positional SDK args and keyword SDK args.

    Applies per-option transforms, dest-renames, const injection, and drops ``None`` options
    so SDK defaults apply. Positional ``args`` are forwarded in declaration order.
    """
    positional = [bound[dest] for dest, _ in cmd.args]
    kwargs: dict[str, Any] = dict(cmd.consts)
    for opt in cmd.options:
        if opt.dest_name in ("json_output_local", "yes") or opt.flag.split()[0] in ("--json",):
            continue
        raw = bound.get(opt.dest_name)
        if raw is None:
            continue
        # Skip boolean filter flags (e.g. --favorites-only) at their default value so the
        # SDK sees None (its own default) rather than an explicit False, which would filter.
        if opt.type == "bool" and raw == opt.default:
            continue
        if opt.transform == "json_file":
            kwargs[opt.dest_name] = _load_definition(raw)
        else:
            kwargs[opt.dest_name] = _apply_transform(opt, raw)
    return positional, kwargs


def _confirm_destructive(cmd: Cmd, assume_yes: bool, *, json_on: bool) -> None:
    """Require ``--yes`` or an interactive confirm for a destructive command.

    Under ``--json`` without ``--yes``, raises :class:`CliError` so the caller emits a
    structured JSON error envelope instead of dropping to an interactive ``[y/N]`` prompt
    on stdout (which would corrupt the machine-readable contract and hang agents).
    """
    if assume_yes:
        return
    if json_on:
        raise CliError(
            "CONFIRMATION_REQUIRED",
            "Pass --yes to confirm this destructive operation.",
        )
    typer.confirm(f"This will {cmd.help.rstrip('.').lower()}. Continue?", abort=True, err=True)


def _emit(cmd: Cmd, resp: Any, bound: dict[str, Any], json_on: bool, *, limit: int) -> None:
    """Render an SDK response according to the command's unwrap mode."""
    if cmd.unwrap == "pager":
        _emit_pager(cmd, resp, json_on, limit=limit)
        return
    if cmd.unwrap == "list":
        _emit_list(cmd, resp, json_on)
        return
    if cmd.unwrap == "action":
        _emit_action(cmd, resp, bound, json_on)
        return
    # default: "data"
    _emit_data(cmd, resp, bound, json_on)


def _emit_pager(cmd: Cmd, pager: Any, json_on: bool, *, limit: int) -> None:
    # The SDK returns a SyncPager when generated with pagination enabled, and a
    # list-envelope model (items under .data) otherwise. Iterating a pydantic
    # envelope directly would yield (field, value) tuples — unwrap .data first.
    # SyncPager has no .data attribute, so this is a no-op for real pagers.
    items = list(islice(iter(getattr(pager, "data", pager)), limit))
    rows = [to_jsonable(item) for item in items]
    if json_on:
        render_json(rows)
        return
    render_table(rows, _columns_for(cmd, rows))


def _emit_list(cmd: Cmd, resp: Any, json_on: bool) -> None:
    data = getattr(resp, "data", resp)
    rows = to_jsonable(data)
    if not isinstance(rows, list):
        rows = [rows] if rows is not None else []
    # Defensive redaction: the server currently returns only key_preview (already masked),
    # but masking _SECRET_FIELDS is forward-compat protection against future API changes.
    if cmd.redact:
        rows = [_redact(row) for row in rows]
    if json_on:
        render_json(rows)
        return
    render_table(rows, _columns_for(cmd, rows))


def _emit_data(cmd: Cmd, resp: Any, bound: dict[str, Any], json_on: bool) -> None:
    data = getattr(resp, "data", resp)
    payload = to_jsonable(data)
    # Defensive redaction (see _emit_list comment).
    if cmd.redact:
        payload = _redact(payload)
    if json_on:
        render_json(payload)
        return
    if cmd.success_msg and isinstance(payload, dict):
        typer.echo(cmd.success_msg.format_map(_fmt_context(payload, bound)))
        return
    _render_keyvalue(payload)


def _emit_action(cmd: Cmd, resp: Any, bound: dict[str, Any], json_on: bool) -> None:
    data = getattr(resp, "data", resp)
    payload = to_jsonable(data)
    identifier = None
    if isinstance(payload, dict):
        identifier = payload.get("id")
    if json_on:
        out: dict[str, Any] = {"ok": True}
        if identifier is not None:
            out["id"] = identifier
        render_json(out)
        return
    message = cmd.success_msg or "Done."
    typer.echo(message.format_map(_fmt_context(payload if isinstance(payload, dict) else {}, bound)))


class _DefaultDict(dict):  # type: ignore[type-arg]
    """dict subclass that returns ``""`` for missing keys, used by ``str.format_map``."""

    def __missing__(self, key: str) -> str:
        return ""


def _fmt_context(payload: dict[str, Any], bound: dict[str, Any]) -> _DefaultDict:
    """Build the substitution namespace for a success_msg (payload fields + bound CLI values).

    Returns a ``_DefaultDict`` so ``str.format_map`` never raises ``KeyError`` on a
    template that references a field absent from the response or the CLI args.
    """
    context = _DefaultDict()
    context.update({key: ("" if value is None else value) for key, value in bound.items()})
    context.update({key: value for key, value in payload.items() if isinstance(key, str)})
    return context


def _columns_for(cmd: Cmd, rows: list[Any]) -> list[str]:
    """Resolve display columns: the declared preset, else the first row's keys."""
    if cmd.columns:
        return cmd.columns
    for row in rows:
        if isinstance(row, dict):
            return list(row.keys())
    return []


def _render_keyvalue(payload: Any) -> None:
    """Render a single model as ``key: value`` lines (nested structures as compact JSON)."""
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(value, (dict, list)):
                typer.echo(f"{key}: {json.dumps(value, default=str)}")
            else:
                typer.echo(f"{key}: {value}")
    else:
        typer.echo(json.dumps(payload, indent=2, default=str))


# Secret field names masked unless --reveal. Explicit list per the security contract.
_SECRET_FIELDS = frozenset({"api_key", "key", "secret", "token", "credentials", "value", "password"})


def _redact(payload: Any) -> Any:
    """Recursively mask secret-bearing fields (keep last 4 chars) unless revealed."""
    if isinstance(payload, dict):
        out: dict[str, Any] = {}
        for key, value in payload.items():
            if isinstance(key, str) and key.lower() in _SECRET_FIELDS and isinstance(value, str) and value:
                out[key] = _mask(value)
            else:
                out[key] = _redact(value)
        return out
    if isinstance(payload, list):
        return [_redact(item) for item in payload]
    return payload


def _mask(secret: str) -> str:
    """Mask a secret to ``****<last4>`` (fully masked if shorter than 4)."""
    if len(secret) <= 4:
        return "****"
    return "****" + secret[-4:]


def make_command(cmd: Cmd) -> Callable[..., None]:
    """Synthesize a native Typer command function from a :class:`Cmd` row.

    Builds an ``inspect.Signature`` (positional Arguments first, then Options) and matching
    ``__annotations__`` so Typer treats the function exactly like a hand-written command.
    """
    params: list[inspect.Parameter] = []
    annotations: dict[str, Any] = {}

    for dest, helptext in cmd.args:
        params.append(
            inspect.Parameter(
                dest,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=typer.Argument(..., help=helptext),
                annotation=str,
            )
        )
        annotations[dest] = str

    for opt in cmd.options:
        flags = opt.flag.split()
        ann = _annotation_for(opt)
        default = (
            typer.Option(opt.default, *flags, help=opt.help)
            if not opt.required
            else typer.Option(..., *flags, help=opt.help)
        )
        params.append(
            inspect.Parameter(opt.dest_name, inspect.Parameter.POSITIONAL_OR_KEYWORD, default=default, annotation=ann)
        )
        annotations[opt.dest_name] = ann

    if cmd.destructive:
        params.append(
            inspect.Parameter(
                "yes",
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=typer.Option(False, "--yes", "-y", help="Skip the confirmation prompt."),
                annotation=bool,
            )
        )
        annotations["yes"] = bool

    def impl(*args: Any, **kwargs: Any) -> None:
        bound_sig = impl.__signature__.bind(*args, **kwargs)  # type: ignore[attr-defined]
        bound_sig.apply_defaults()
        bound = dict(bound_sig.arguments)
        _run(cmd, bound)

    impl.__name__ = (cmd.name.replace("-", "_") + "_" + (cmd.subgroup or cmd.group)).replace("-", "_")
    impl.__signature__ = inspect.Signature(params)  # type: ignore[attr-defined]
    impl.__annotations__ = annotations
    impl.__doc__ = cmd.help
    return impl


def _run(cmd: Cmd, bound: dict[str, Any]) -> None:
    """Execute a synthesized command: resolve client, transform, call SDK, emit."""
    json_on = output_json(bool(bound.get("json_output_local", False)))

    limit = _resolve_limit(cmd, bound, json_on)

    with api_errors(json_on):
        if cmd.destructive:
            _confirm_destructive(cmd, bool(bound.get("yes", False)), json_on=json_on)

        client = get_client()
        method = _resolve_method(client, cmd.method_paths)
        positional, kwargs = _build_kwargs(cmd, bound)
        if _accepts_workspace_kwarg(method):
            workspace = _state.root_options.get("workspace")
            if workspace:
                kwargs["workspace_id"] = workspace
        try:
            resp = method(*positional, **kwargs)
        except Exception as exc:  # noqa: BLE001 - 404 idempotency for delete --yes only
            if _is_idempotent_delete(cmd) and bound.get("yes") and _is_not_found(exc):
                _emit_idempotent(cmd, bound, json_on)
                return
            raise
        _emit(cmd, resp, bound, json_on, limit=limit)


def _resolve_limit(cmd: Cmd, bound: dict[str, Any], json_on: bool) -> int:
    """Validate and return the pager ``--limit`` (>=1); raises usage exit 2 if invalid."""
    if cmd.unwrap != "pager":
        return 0
    limit = bound.get("limit")
    if limit is None:
        return 50
    if limit < 1:
        # Usage error -> exit code 2, matching Typer's parameter-validation contract.
        raise typer.BadParameter("--limit must be >= 1.")
    return int(limit)


def _is_idempotent_delete(cmd: Cmd) -> bool:
    """True only for delete operations, which are safe to treat as idempotent on 404.

    A delete whose target is already gone is effectively a success. Other destructive
    ops are NOT repeat-safe: ``runs cancel``/``members remove``/``revoke-invite`` returning
    404 means a wrong id or workspace, which must surface as an error rather than a phantom
    success (automation would otherwise believe the operation happened).
    """
    leaf = cmd.method.rsplit(".", 1)[-1]
    return cmd.destructive and (leaf == "delete" or leaf.startswith("delete_"))


def _is_not_found(exc: Exception) -> bool:
    """True if an exception represents a 404 (used for delete idempotency)."""
    from onepin.errors import NotFoundError

    if isinstance(exc, NotFoundError):
        return True
    return getattr(exc, "status_code", None) == 404


def _emit_idempotent(cmd: Cmd, bound: dict[str, Any], json_on: bool) -> None:
    """Emit a stable success for a delete whose target was already gone (404)."""
    if json_on:
        render_json({"ok": True})
        return
    message = cmd.success_msg or "Done."
    typer.echo(message.format_map(_fmt_context({}, bound)))


def build(app: typer.Typer, cmd: Cmd) -> None:
    """Register one synthesized command from a :class:`Cmd` row onto ``app``."""
    fn = make_command(cmd)
    app.command(cmd.name, help=cmd.help)(fn)
