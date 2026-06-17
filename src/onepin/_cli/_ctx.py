"""Lazy SDK context: credential resolution, client construction, error mapping, and output helpers.

This module is the bridge between the table-driven dispatcher and the Fern-generated SDK.
It is intentionally cheap to import: ``from onepin.client import OnePinClient`` is deferred
inside :func:`build_client` / :func:`get_client` so that ``onepin --help`` and ``onepin login``
never pull in the SDK. A fast-startup test asserts this.
"""

from __future__ import annotations

import datetime as dt
import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator
from urllib.parse import urlparse

import click

from onepin._cli import _state
from onepin._cli._http import OnePinAuthError, _parse_error_envelope
from onepin._cli.auth.resolver import ResolvedCredentials, resolve_credentials

if TYPE_CHECKING:  # pragma: no cover - type-only import, never loaded at runtime
    from onepin.client import OnePinClient

_DEFAULT_BASE_URL = "https://api.onepin.ai"


class CliError(Exception):
    """A handled CLI failure mapped to a stable error code.

    Raised by the dispatcher and composites for any local or API failure that should
    exit ``1`` with a structured message. Never carries a traceback to the user.
    """

    def __init__(self, code: str, message: str, *, request_id: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.request_id = request_id


def build_client(creds: ResolvedCredentials) -> OnePinClient:
    """Build an OnePinClient from resolved credentials.

    The API key is passed as the SDK ``token`` (sent as ``Authorization: Bearer``); a
    custom ``--base-url`` is passed straight through, and an empty one falls back to the
    default production environment. An API key is required -- this raises rather than
    building an unauthenticated client.

    Args:
        creds: Resolved credentials from the priority chain.

    Returns:
        A configured OnePinClient.

    Raises:
        OnePinAuthError: If no API key is available, or the base URL is not http(s)
            (guards against sending the token to a ``file://``/``ftp://`` host).
    """
    # Deferred import: importing _ctx must stay cheap (no SDK on `onepin --help`).
    # make_client wraps OnePinClient with the version-gate response hook + a corrected
    # User-Agent (the generated default is baked at codegen time and can be stale).
    from onepin._version_gate import make_client

    if not creds.api_key:
        raise OnePinAuthError(
            "Not logged in. Run `onepin login`, set ONEPIN_API_KEY, or pass --api-key.",
            error_code="NOT_AUTHENTICATED",
        )
    if creds.base_url and urlparse(creds.base_url).scheme not in ("http", "https"):
        raise OnePinAuthError(
            f"Invalid base URL {creds.base_url!r}: only http and https are supported.",
            error_code="INVALID_BASE_URL",
        )
    return make_client(base_url=creds.base_url, token=creds.api_key)


def _is_commandline_source(value: object) -> bool:
    return value == click.core.ParameterSource.COMMANDLINE or getattr(value, "name", None) == "COMMANDLINE"


def resolve_cli_credentials() -> ResolvedCredentials:
    """Resolve credentials honoring the root ``--api-key`` / ``--base-url`` flags.

    Reads the captured root-callback state to determine whether ``--api-key`` /
    ``--base-url`` were passed on the command line (vs. sourced from an env var), so the
    resolver attributes ``source`` correctly (``flag`` vs ``env`` vs ``file``). This is the
    shared logic that both ``whoami`` and the dispatcher use.

    Returns:
        ResolvedCredentials from the priority chain (flag > env > file > default).
    """
    root_options = _state.root_options
    flag_api_key: str | None = None
    flag_base_url: str | None = None
    if _is_commandline_source(root_options.get("api_key_source")):
        flag_api_key = root_options.get("api_key")
    if _is_commandline_source(root_options.get("base_url_source")):
        flag_base_url = root_options.get("base_url")
    return resolve_credentials(flag_api_key=flag_api_key, flag_base_url=flag_base_url)


def get_client() -> OnePinClient:
    """Resolve credentials and build an authenticated client.

    Returns:
        A configured OnePinClient.

    Raises:
        OnePinAuthError: If no credentials are available or the base URL is invalid.
    """
    return build_client(resolve_cli_credentials())


def output_json(local: bool) -> bool:
    """Return True if JSON output is requested.

    Honors either the root ``--json`` callback flag or a per-command ``--json`` flag.

    Args:
        local: Value of the per-command ``--json`` flag.

    Returns:
        True if either the root or local JSON flag is set.
    """
    return bool(local or _state.root_options.get("json_output", False))


def to_jsonable(obj: Any) -> Any:
    """Recursively convert SDK models / containers / datetimes to JSON-serializable values.

    Pydantic models are dumped via ``model_dump(mode="json")`` (which itself handles nested
    models and datetimes). Lists/tuples and dicts are walked. ``datetime``/``date`` become
    ISO strings. Everything else is returned unchanged.

    Args:
        obj: Any SDK response, model, container, or scalar.

    Returns:
        A value composed only of dict/list/str/int/float/bool/None.
    """
    model_dump = getattr(obj, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json")
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(item) for item in obj]
    if isinstance(obj, dict):
        return {key: to_jsonable(value) for key, value in obj.items()}
    if isinstance(obj, (dt.datetime, dt.date)):
        return obj.isoformat()
    return obj


@contextmanager
def api_errors(json_out: bool) -> Iterator[None]:
    """Map SDK / network / local errors to structured CLI output and exit codes.

    Catches the documented exception set and renders either a ``[CODE] message`` line to
    stderr (default) or a structured ``{"error": ..., "meta": ...}`` JSON envelope to stderr
    (when ``json_out``), then exits ``1``. ``KeyboardInterrupt`` exits ``130``.
    ``BrokenPipeError`` exits ``0`` cleanly. SDK error imports are deferred so importing
    this module stays cheap.

    Args:
        json_out: Whether to emit the structured-JSON error envelope.
    """
    # Deferred: these SDK error classes live under the generated tree.
    from onepin._version_gate import OnePinUpgradeRequiredError
    from onepin.core.api_error import ApiError
    from onepin.core.parse_error import ParsingError
    from onepin.errors import ConflictError, NotFoundError, UnprocessableEntityError

    try:
        yield
    except KeyboardInterrupt:
        _emit_error("INTERRUPTED", "Interrupted.", None, json_out)
        raise SystemExit(130) from None
    except BrokenPipeError:
        # Downstream closed the pipe (e.g. `| head`). Exit cleanly, no error.
        raise SystemExit(0) from None
    except CliError as exc:
        _emit_error(exc.code, exc.message, exc.request_id, json_out)
        raise SystemExit(1) from exc
    except OnePinAuthError as exc:
        _emit_error(exc.error_code, exc.message, exc.request_id, json_out)
        raise SystemExit(1) from exc
    except ParsingError as exc:
        # Fern raises ParsingError when a 2xx response body doesn't match the expected
        # schema. Map to a generic error -- do NOT dump raw response internals.
        _emit_error(
            "INVALID_RESPONSE",
            "The API returned an unexpected response format.",
            None,
            json_out,
        )
        raise SystemExit(1) from exc
    except OnePinUpgradeRequiredError as exc:
        # Client-side gate (response hook) saw an install below the required floor.
        _emit_upgrade_required(str(exc), json_out)
        raise SystemExit(1) from exc
    except (NotFoundError, ConflictError, UnprocessableEntityError, ApiError) as exc:
        # 426 Upgrade Required: the server hard-floors the SDK version. Surface it as the
        # same yellow upgrade message instead of a generic API error.
        if getattr(exc, "status_code", None) == 426:
            _emit_upgrade_required(_format_upgrade_required(exc), json_out)
            raise SystemExit(1) from exc
        code, message, request_id = _classify_api_error(exc)
        _emit_error(code, message, request_id, json_out)
        raise SystemExit(1) from exc
    except Exception as exc:  # noqa: BLE001 - final mapping of network / local failures
        maybe_code, message = _classify_other_error(exc)
        if maybe_code is None:
            raise
        _emit_error(maybe_code, message, None, json_out)
        raise SystemExit(1) from exc


def _classify_api_error(exc: Exception) -> tuple[str, str, str | None]:
    """Extract (code, message, request_id) from an SDK ApiError using the shared envelope parser."""
    status = getattr(exc, "status_code", None)
    body = getattr(exc, "body", None)
    parsed = _parse_error_envelope(body)
    code = parsed.get("code") if parsed else None
    message = parsed.get("message") if parsed else None
    request_id = parsed.get("request_id") if parsed else None
    if not code:
        code = _status_code_name(status)
    if not message:
        message = _status_message(status)
    return code, message, request_id


def _status_code_name(status: int | None) -> str:
    mapping = {
        400: "BAD_REQUEST",
        401: "INVALID_API_KEY",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
    }
    if status is None:
        return "API_ERROR"
    if status in mapping:
        return mapping[status]
    if status >= 500:
        return "SERVER_ERROR"
    return "API_ERROR"


def _status_message(status: int | None) -> str:
    if status is None:
        return "API request failed."
    return f"API request failed with status {status}."


def _classify_other_error(exc: Exception) -> tuple[str | None, str]:
    """Map network / file / decode / validation errors to (code, message).

    Returns ``(None, ...)`` for unrecognized exceptions so the caller re-raises (surfacing
    a real bug rather than swallowing it).
    """
    import json

    import httpx
    from pydantic import ValidationError

    if isinstance(exc, httpx.ConnectError):
        return "NETWORK_ERROR", "Could not connect to the OnePin API."
    if isinstance(exc, httpx.TimeoutException):
        return "TIMEOUT", "The request to the OnePin API timed out."
    if isinstance(exc, httpx.TransportError):
        return "NETWORK_ERROR", "A network transport error occurred."
    if isinstance(exc, json.JSONDecodeError):
        return "INVALID_JSON", f"Could not parse JSON: {exc}"
    if isinstance(exc, ValidationError):
        return "VALIDATION_ERROR", _format_validation_error(exc)
    if isinstance(exc, FileNotFoundError):
        return "FILE_NOT_FOUND", f"File not found: {exc.filename or exc}"
    if isinstance(exc, IsADirectoryError):
        return "FILE_NOT_FOUND", f"Expected a file but found a directory: {exc.filename or exc}"
    if isinstance(exc, PermissionError):
        return "PERMISSION_DENIED", f"Permission denied: {exc.filename or exc}"
    return None, str(exc)


def _format_validation_error(exc: Any) -> str:
    """Render a pydantic ValidationError as a compact, single-line, human message."""
    parts = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err.get("loc", ())) or "(root)"
        parts.append(f"{loc}: {err.get('msg', 'invalid')}")
    return "Invalid input -- " + "; ".join(parts)


def _emit_error(code: str, message: str, request_id: str | None, json_out: bool) -> None:
    """Write a structured error to stderr (JSON envelope when ``json_out``, else a tagged line)."""
    if json_out:
        import json

        envelope: dict[str, Any] = {"error": {"code": code, "message": message}}
        if request_id:
            envelope["meta"] = {"request_id": request_id}
        print(json.dumps(envelope, indent=2), file=sys.stderr)
    else:
        rid = f" (request_id={request_id})" if request_id else ""
        print(f"[{code}] {message}{rid}", file=sys.stderr)


def _emit_upgrade_required(message: str, json_out: bool) -> None:
    """Emit a version-floor failure: machine envelope under --json, else a yellow stderr note."""
    if json_out:
        _emit_error("UPGRADE_REQUIRED", message, None, json_out)
        return
    from onepin._cli.render import echo_warning

    echo_warning(message)


def _format_upgrade_required(exc: Exception) -> str:
    """Build an upgrade message from a 426 ApiError body (best-effort), else a generic one."""
    from onepin._version_gate import format_upgrade_message

    required = None
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        detail = body.get("error") if isinstance(body.get("error"), dict) else body
        if isinstance(detail, dict):
            raw = detail.get("required_version") or detail.get("minimum_version")
            required = raw.strip() if isinstance(raw, str) and raw.strip() else None
    return format_upgrade_message(required)
