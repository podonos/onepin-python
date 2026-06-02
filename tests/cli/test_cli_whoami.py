"""Tests for `onepin whoami` command."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx
from typer.testing import CliRunner

from onepin._cli.main import app

runner = CliRunner()

_WHOAMI_URL = "https://api.onepin.ai/api/v1/auth/whoami"

_WHOAMI_RESPONSE = {
    "data": {
        "auth_kind": "api_key",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "workspace_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "api_key_id": "00000000-0000-0000-0000-000000000002",
        "scopes": ["workflows:read", "voices:read"],
    },
    "meta": {"request_id": "01JTEST00000000000000000000", "timestamp": "2025-01-01T00:00:00Z"},
}


def _write_credentials(tmp_home: Path, api_key: str = "op_live_filekey") -> None:
    creds_dir = tmp_home / ".onepin"
    creds_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    (creds_dir / "credentials").write_text(f'[default]\napi_key = "{api_key}"\nbase_url = "https://api.onepin.ai"\n')


class TestWhoamiNotLoggedIn:
    def test_no_creds_exits_1_with_not_logged_in(self, tmp_home: Path) -> None:
        """No flag, no env, no file → exits 1, prints [NOT_LOGGED_IN]."""
        result = runner.invoke(app, ["whoami"])

        assert result.exit_code == 1
        assert "NOT_LOGGED_IN" in result.output
        assert "onepin login" in result.output


class TestWhoamiSources:
    @respx.mock
    def test_source_flag(self, tmp_home: Path) -> None:
        """Key from --api-key flag → prints Source: flag."""
        respx.get(_WHOAMI_URL).mock(return_value=httpx.Response(200, json=_WHOAMI_RESPONSE))

        result = runner.invoke(app, ["--api-key", "op_live_flagkey", "whoami"])

        assert result.exit_code == 0, result.output
        assert "Source: flag" in result.output

    @respx.mock
    def test_source_env(self, tmp_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Key from ONEPIN_API_KEY env var → prints Source: env."""
        monkeypatch.setenv("ONEPIN_API_KEY", "op_live_envkey")
        respx.get(_WHOAMI_URL).mock(return_value=httpx.Response(200, json=_WHOAMI_RESPONSE))

        result = runner.invoke(app, ["whoami"])

        assert result.exit_code == 0, result.output
        assert "Source: env" in result.output

    @respx.mock
    def test_source_file(self, tmp_home: Path) -> None:
        """Key from credentials file → prints Source: file."""
        _write_credentials(tmp_home)
        respx.get(_WHOAMI_URL).mock(return_value=httpx.Response(200, json=_WHOAMI_RESPONSE))

        result = runner.invoke(app, ["whoami"])

        assert result.exit_code == 0, result.output
        assert "Source: file" in result.output


class TestWhoamiOutput:
    @respx.mock
    def test_prints_workspace_and_scopes(self, tmp_home: Path) -> None:
        """Successful whoami prints workspace UUID and scopes."""
        _write_credentials(tmp_home)
        respx.get(_WHOAMI_URL).mock(return_value=httpx.Response(200, json=_WHOAMI_RESPONSE))

        result = runner.invoke(app, ["whoami"])

        assert result.exit_code == 0, result.output
        assert "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" in result.output
        assert "workflows:read" in result.output
        assert "voices:read" in result.output
        assert "Base URL: https://api.onepin.ai" in result.output
        assert "Auth: api_key" in result.output

    @respx.mock
    def test_json_output(self, tmp_home: Path) -> None:
        """`onepin --json whoami` emits the whoami data as JSON."""
        _write_credentials(tmp_home)
        respx.get(_WHOAMI_URL).mock(return_value=httpx.Response(200, json=_WHOAMI_RESPONSE))

        result = runner.invoke(app, ["--json", "whoami"])

        assert result.exit_code == 0, result.output
        assert '"workspace_id"' in result.output


class TestWhoamiErrors:
    @respx.mock
    def test_invalid_key_exits_1(self, tmp_home: Path) -> None:
        _write_credentials(tmp_home)
        body = {"error": {"code": "INVALID_API_KEY", "message": "rejected"}, "meta": {"request_id": "r5"}}
        respx.get(_WHOAMI_URL).mock(return_value=httpx.Response(401, json=body))

        result = runner.invoke(app, ["whoami"])

        assert result.exit_code == 1
        assert "INVALID_API_KEY" in result.output

    @respx.mock
    def test_network_error_exits_1(self, tmp_home: Path) -> None:
        _write_credentials(tmp_home)
        respx.get(_WHOAMI_URL).mock(side_effect=httpx.ConnectError("down"))

        result = runner.invoke(app, ["whoami"])

        assert result.exit_code == 1
        assert "NETWORK_ERROR" in result.output

    @respx.mock
    def test_server_error_exits_1(self, tmp_home: Path) -> None:
        _write_credentials(tmp_home)
        body = {"error": {"code": "SERVER_ERROR", "message": "boom"}}
        respx.get(_WHOAMI_URL).mock(return_value=httpx.Response(500, json=body))

        result = runner.invoke(app, ["whoami"])

        assert result.exit_code == 1
        assert "SERVER_ERROR" in result.output


class TestWhoamiJsonErrors:
    """Under --json, every whoami failure must emit a structured JSON error envelope."""

    def test_no_creds_json_envelope(self, tmp_home: Path) -> None:
        result = runner.invoke(app, ["--json", "whoami"])
        assert result.exit_code == 1
        assert '"code": "NOT_LOGGED_IN"' in result.output
        assert '"message"' in result.output

    @respx.mock
    def test_401_json_envelope(self, tmp_home: Path) -> None:
        _write_credentials(tmp_home)
        body = {"error": {"code": "INVALID_API_KEY", "message": "rejected"}, "meta": {"request_id": "r9"}}
        respx.get(_WHOAMI_URL).mock(return_value=httpx.Response(401, json=body))

        result = runner.invoke(app, ["--json", "whoami"])

        assert result.exit_code == 1
        assert '"code": "INVALID_API_KEY"' in result.output
        assert '"request_id": "r9"' in result.output

    @respx.mock
    def test_network_error_json_envelope(self, tmp_home: Path) -> None:
        _write_credentials(tmp_home)
        respx.get(_WHOAMI_URL).mock(side_effect=httpx.ConnectError("down"))

        result = runner.invoke(app, ["--json", "whoami"])

        assert result.exit_code == 1
        assert '"code": "NETWORK_ERROR"' in result.output
