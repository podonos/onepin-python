"""Login / logout / whoami commands."""

from __future__ import annotations

import json
import os

import click
import typer

from onepin._cli import _state
from onepin._cli._http import OnePinAuthError, OnePinHTTPError, OnePinNetworkError, _call_whoami
from onepin._cli.auth.credentials import delete_credentials, write_credentials
from onepin._cli.auth.resolver import resolve_credentials

_DEFAULT_BASE_URL = "https://api.onepin.ai"
_DASHBOARD_URL = "https://app.onepin.ai/settings/api-keys"


def _is_commandline_source(value: object) -> bool:
    return value == click.core.ParameterSource.COMMANDLINE or getattr(value, "name", None) == "COMMANDLINE"


def _resolve_base_url(flag: str | None) -> str:
    return flag or os.environ.get("ONEPIN_BASE_URL") or _DEFAULT_BASE_URL


def login(
    key: str | None = typer.Option(None, "--key", help="API key. Prompts if omitted."),
    base_url: str | None = typer.Option(None, "--base-url"),
) -> None:
    """Validate an API key and write it to ~/.onepin/credentials."""
    resolved_base_url = _resolve_base_url(base_url)

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
    try:
        data = _call_whoami(key, resolved_base_url)
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


def whoami(ctx: typer.Context) -> None:
    """Show active auth source + workspace UUID + scopes."""
    # Read global flags (--api-key, --base-url, --json) from the root app callback context.
    # Only treat api_key as an explicit flag when it was passed on the command line (not env var),
    # so that resolve_credentials() can correctly attribute source="env" vs source="flag".
    flag_api_key: str | None = None
    flag_base_url: str | None = None
    json_output = False
    try:
        root_options = _state.root_options
        parent = ctx.parent
        if parent is not None:
            root_options = {
                **root_options,
                "api_key": parent.params.get("api_key"),
                "api_key_source": root_options.get("api_key_source") or parent.get_parameter_source("api_key"),
                "base_url": parent.params.get("base_url"),
                "base_url_source": root_options.get("base_url_source") or parent.get_parameter_source("base_url"),
                "json_output": parent.params.get("json_output", root_options.get("json_output", False)),
            }
        if _is_commandline_source(root_options.get("api_key_source")):
            flag_api_key = root_options.get("api_key")
        if _is_commandline_source(root_options.get("base_url_source")):
            flag_base_url = root_options.get("base_url")
        json_output = bool(root_options.get("json_output", False))
    except Exception:  # noqa: BLE001
        pass

    creds = resolve_credentials(flag_api_key=flag_api_key, flag_base_url=flag_base_url)

    if not creds.api_key:
        typer.echo(
            "[NOT_LOGGED_IN] Run `onepin login` or set ONEPIN_API_KEY.",
            err=True,
        )
        raise typer.Exit(code=1)

    resolved_base_url = creds.base_url or _DEFAULT_BASE_URL

    try:
        data = _call_whoami(creds.api_key, resolved_base_url)
    except OnePinAuthError as exc:
        rid = f", request_id={exc.request_id}" if exc.request_id else ""
        typer.echo(f"[INVALID_API_KEY] {exc.message}{rid}", err=True)
        raise typer.Exit(code=1)
    except OnePinNetworkError as exc:
        typer.echo(f"[NETWORK_ERROR] {exc.message}", err=True)
        raise typer.Exit(code=1)
    except OnePinHTTPError as exc:
        rid = f", request_id={exc.request_id}" if exc.request_id else ""
        typer.echo(f"[{exc.error_code}] {exc.message}{rid}", err=True)
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
