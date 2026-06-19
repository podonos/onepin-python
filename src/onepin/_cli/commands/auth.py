"""Login / logout / whoami commands."""

from __future__ import annotations

import json
import os

import typer

from onepin._cli import _state
from onepin._cli._http import OnePinAuthError, OnePinHTTPError, OnePinNetworkError, _call_whoami
from onepin._cli.auth.credentials import delete_credentials, write_credentials

_DEFAULT_BASE_URL = "https://api.onepin.ai"
_DASHBOARD_URL = "https://app.onepin.ai/workspace/~/settings/api"


def _resolve_login_base_url(local_flag: str | None) -> str:
    """Resolve base_url for login: local --base-url > root --base-url > env > default.

    Login has its own ``--base-url`` parameter, but the root ``--base-url`` (stored in
    ``_state.root_options``) should also be honored when the user passes it there instead.
    """
    import click

    if local_flag is not None:
        return local_flag
    # Root --base-url (only when explicitly passed on the command line).
    root = _state.root_options
    root_source = root.get("base_url_source")
    is_cmdline = (
        root_source == click.core.ParameterSource.COMMANDLINE or getattr(root_source, "name", None) == "COMMANDLINE"
    )
    if is_cmdline and root.get("base_url"):
        return str(root["base_url"])
    return os.environ.get("ONEPIN_BASE_URL") or _DEFAULT_BASE_URL


def login(
    key: str | None = typer.Option(None, "--key", help="API key. Prompts if omitted."),
    base_url: str | None = typer.Option(None, "--base-url"),
) -> None:
    """Validate an API key and write it to ~/.onepin/credentials."""
    resolved_base_url = _resolve_login_base_url(base_url)

    # Resolve key: flag or interactive prompt
    if key is None:
        key = typer.prompt("API key", hide_input=True)

    # Pre-flight: key format check (before any network call)
    if not key.startswith("op_live_"):
        typer.echo(
            f"[INVALID_API_KEY] Key must start with op_live_. Generate one at {_DASHBOARD_URL}",
            err=True,
        )
        raise typer.Exit(code=1)

    # Validate against /api/v1/auth/whoami
    verbose = bool(_state.root_options.get("verbose", False))
    try:
        data = _call_whoami(key, resolved_base_url, verbose=verbose)
    except OnePinAuthError:
        typer.echo(
            f"[INVALID_API_KEY] Key rejected. Generate one at {_DASHBOARD_URL}",
            err=True,
        )
        raise typer.Exit(code=1)
    except OnePinNetworkError as exc:
        typer.echo(f"[NETWORK_ERROR] {exc.message}", err=True)
        raise typer.Exit(code=1)
    except OnePinHTTPError as exc:
        rid = f", request_id={exc.request_id}" if exc.request_id else ""
        typer.echo(f"[{exc.error_code}] {exc.message}{rid}", err=True)
        raise typer.Exit(code=1)

    # Persist credentials
    write_credentials(api_key=key, base_url=resolved_base_url)

    workspace_id = data.get("workspace_id", "")
    scopes = data.get("scopes", [])
    scopes_str = ", ".join(scopes) if scopes else "(none)"

    typer.echo("✓ Logged in.")
    typer.echo(f"  Workspace: {workspace_id}")
    typer.echo(f"  Scopes: {scopes_str}")
    typer.echo("  Saved to ~/.onepin/credentials")


def logout() -> None:
    """Remove ~/.onepin/credentials."""
    delete_credentials()  # returns bool; idempotent -- no error if missing
    typer.echo("✓ Removed credentials.")


def whoami() -> None:
    """Show active auth source + workspace UUID + scopes."""
    # Credential resolution (flag > env > file) is shared with the dispatcher: it reads the
    # root-callback state to attribute source correctly (flag vs env vs file).
    from onepin._cli._ctx import _emit_error, resolve_cli_credentials

    json_output = bool(_state.root_options.get("json_output", False))
    creds = resolve_cli_credentials()

    if not creds.api_key:
        _emit_error("NOT_LOGGED_IN", "Run `onepin login` or set ONEPIN_API_KEY.", None, json_output)
        raise typer.Exit(code=1)

    resolved_base_url = creds.base_url or _DEFAULT_BASE_URL
    verbose = bool(_state.root_options.get("verbose", False))

    try:
        data = _call_whoami(creds.api_key, resolved_base_url, verbose=verbose)
    except OnePinAuthError as exc:
        _emit_error("INVALID_API_KEY", exc.message, exc.request_id, json_output)
        raise typer.Exit(code=1)
    except OnePinNetworkError as exc:
        _emit_error("NETWORK_ERROR", exc.message, None, json_output)
        raise typer.Exit(code=1)
    except OnePinHTTPError as exc:
        _emit_error(exc.error_code, exc.message, exc.request_id, json_output)
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(data, indent=2))
        return

    workspace_id = data.get("workspace_id", "")
    auth_kind = data.get("auth_kind", "")
    scopes = data.get("scopes", [])
    scopes_str = ", ".join(scopes) if scopes else "(none)"

    typer.echo(f"Source: {creds.source}")
    typer.echo(f"Base URL: {resolved_base_url}")
    typer.echo(f"Auth: {auth_kind}")
    typer.echo(f"Workspace: {workspace_id}")
    typer.echo(f"Scopes: {scopes_str}")
