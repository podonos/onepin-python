"""Behavioral tests for global CLI flags (onepin._cli.main).

These exercise the flags through the real CLI rather than unit-testing the
process-local state dict or the command registry directly.
"""

from __future__ import annotations

import os

import httpx
import respx
from typer.testing import CliRunner

from onepin._cli import _state
from onepin._cli.main import app

runner = CliRunner()

_WHOAMI_URL = "https://api.onepin.ai/api/v1/auth/whoami"
_WHOAMI_RESPONSE = {
    "data": {"auth_kind": "api_key", "workspace_id": "ws-1", "scopes": ["read"]},
    "meta": {"request_id": "01JTEST00000000000000000000", "timestamp": "2025-01-01T00:00:00Z"},
}


def test_all_subcommands_registered(tmp_home) -> None:
    """Every subcommand group is wired onto the root app (covers _registry)."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for name in ("login", "logout", "whoami", "workflows", "voices", "templates", "uploads"):
        assert name in result.output


def test_no_color_disables_color(tmp_home, monkeypatch) -> None:
    """--no-color disables color via captured state, with no global env mutation."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    from onepin._cli import _state, render

    result = runner.invoke(app, ["--no-color", "logout"])
    assert result.exit_code == 0
    assert _state.root_options.get("no_color") is True
    assert render._use_color() is False
    assert "NO_COLOR" not in os.environ


@respx.mock
def test_verbose_logs_http(tmp_home, monkeypatch) -> None:
    """--verbose logs the HTTP request/response to stderr; previously dropped."""
    monkeypatch.setenv("ONEPIN_API_KEY", "op_live_x")
    respx.get(_WHOAMI_URL).mock(return_value=httpx.Response(200, json=_WHOAMI_RESPONSE))
    result = runner.invoke(app, ["--verbose", "whoami"])
    assert result.exit_code == 0, result.output
    assert "GET" in result.output
    assert "200" in result.output


@respx.mock
def test_debug_implies_verbose(tmp_home, monkeypatch) -> None:
    """--debug enables verbose HTTP logging (debug implies verbose)."""
    monkeypatch.setenv("ONEPIN_API_KEY", "op_live_x")
    respx.get(_WHOAMI_URL).mock(return_value=httpx.Response(200, json=_WHOAMI_RESPONSE))
    result = runner.invoke(app, ["--debug", "whoami"])
    assert result.exit_code == 0, result.output
    assert "GET" in result.output


@respx.mock
def test_workspace_flag_stored_not_dropped(tmp_home, monkeypatch) -> None:
    """--workspace is captured in root state (consumed once commands hit the API)."""
    monkeypatch.setenv("ONEPIN_API_KEY", "op_live_x")
    respx.get(_WHOAMI_URL).mock(return_value=httpx.Response(200, json=_WHOAMI_RESPONSE))
    runner.invoke(app, ["--workspace", "ws-42", "whoami"])
    assert _state.root_options.get("workspace") == "ws-42"
