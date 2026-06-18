"""``onepin health`` -- liveness/readiness probes plus the version/status surface.

Beyond the probe status, this reports the installed SDK version, the API's reported version,
the recommended version (latest on PyPI, from the upgrade-check cache -- no network here), and
the required floor (the ``X-OnePin-Required-Version`` response header). Hand-written (rather than
table-driven) so it can blend local, cached, and header-sourced facts into one view.
"""

from __future__ import annotations

from typing import Any, Optional

import typer

from onepin._cli import __version__
from onepin._cli._ctx import api_errors, get_client, output_json
from onepin._cli.render import render_json
from onepin._version_gate import required_version_from

# (info key, human label) in display order.
_FIELDS = [
    ("status", "status"),
    ("sdk_version", "SDK version"),
    ("api_version", "API version"),
    ("recommended_version", "Recommended SDK version"),
    ("required_version", "Required SDK version"),
]


def _recommended() -> Optional[str]:
    """Latest version from the upgrade-check cache (no network); None if never checked."""
    from onepin._cli._update_check import cached_latest

    return cached_latest()


def _build_info(data: Any, headers: Any) -> dict[str, Optional[str]]:
    body = data if isinstance(data, dict) else {}
    status = body.get("status") or "ok"
    return {
        "status": status,
        "sdk_version": __version__,
        "api_version": body.get("version"),
        "recommended_version": _recommended(),
        "required_version": required_version_from(headers),
    }


def _emit(info: dict[str, Optional[str]], json_on: bool) -> None:
    if json_on:
        render_json({key: value for key, value in info.items() if value is not None})
        return
    for key, label in _FIELDS:
        value = info.get(key)
        typer.echo(f"{label}: {value if value is not None else 'unknown'}")


def live(
    json_output_local: bool = typer.Option(False, "--json", help="Emit JSON instead of a table."),
) -> None:
    """Liveness probe."""
    json_on = output_json(json_output_local)
    with api_errors(json_on):
        client = get_client()
        response = client.health.with_raw_response.liveness()
        _emit(_build_info(response.data, response.headers), json_on)


def ready(
    json_output_local: bool = typer.Option(False, "--json", help="Emit JSON instead of a table."),
) -> None:
    """Readiness probe."""
    json_on = output_json(json_output_local)
    with api_errors(json_on):
        client = get_client()
        response = client.health.with_raw_response.readiness()
        _emit(_build_info(response.data, response.headers), json_on)
