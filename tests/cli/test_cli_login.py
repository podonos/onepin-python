"""Tests for `onepin login` command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import httpx
import respx
from typer.testing import CliRunner

from onepin._cli.main import app

runner = CliRunner()

_WHOAMI_URL = "https://api.onepin.ai/api/v1/auth/whoami"
_DEV_WHOAMI_URL = "https://dev-api.onepin.ai/api/v1/auth/whoami"

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


class TestLoginHappyPath:
    @respx.mock
    def test_key_flag_writes_file_and_prints_workspace(self, tmp_home: Path) -> None:
        """--key op_live_xxx happy path: writes credentials, prints workspace UUID + scopes."""
        respx.get(_WHOAMI_URL).mock(return_value=httpx.Response(200, json=_WHOAMI_RESPONSE))

        result = runner.invoke(app, ["login", "--key", "op_live_testkey123"])

        assert result.exit_code == 0, result.output
        assert "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" in result.output
        assert "workflows:read" in result.output
        assert "voices:read" in result.output
        assert "~/.onepin/credentials" in result.output

        creds_path = tmp_home / ".onepin" / "credentials"
        assert creds_path.exists()
        content = creds_path.read_text()
        assert "op_live_testkey123" in content
        assert "https://api.onepin.ai" in content

    @respx.mock
    def test_prompt_path_accepts_pasted_key(self, tmp_home: Path) -> None:
        """No --key flag: prompt reads key from stdin."""
        respx.get(_WHOAMI_URL).mock(return_value=httpx.Response(200, json=_WHOAMI_RESPONSE))

        result = runner.invoke(app, ["login"], input="op_live_promptkey\n")

        assert result.exit_code == 0, result.output
        assert "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" in result.output

        creds_path = tmp_home / ".onepin" / "credentials"
        assert creds_path.exists()

    @respx.mock
    def test_custom_base_url_written_to_credentials(self, tmp_home: Path) -> None:
        """--base-url flag is persisted in credentials file."""
        respx.get(_DEV_WHOAMI_URL).mock(return_value=httpx.Response(200, json=_WHOAMI_RESPONSE))

        result = runner.invoke(
            app,
            ["login", "--key", "op_live_devkey", "--base-url", "https://dev-api.onepin.ai"],
        )

        assert result.exit_code == 0, result.output
        creds_path = tmp_home / ".onepin" / "credentials"
        content = creds_path.read_text()
        assert "https://dev-api.onepin.ai" in content


class TestLoginInvalidKeyFormat:
    def test_key_not_starting_with_op_live_exits_1(self, tmp_home: Path) -> None:
        """Key that doesn't start with op_live_ exits 1 BEFORE any network call."""
        # No respx mock: if httpx is called the test will raise (unexpected call)
        result = runner.invoke(app, ["login", "--key", "sk_not_valid_key"])

        assert result.exit_code == 1
        assert "INVALID_API_KEY" in result.output
        assert "op_live_" in result.output

    def test_key_not_starting_with_op_live_makes_no_network_call(self, tmp_home: Path) -> None:
        """Confirm no HTTP request is made for bad-format keys."""
        call_count = 0

        original_get = httpx.Client.get

        def tracking_get(self, url, **kwargs):  # type: ignore[override]
            nonlocal call_count
            call_count += 1
            return original_get(self, url, **kwargs)

        with patch.object(httpx.Client, "get", tracking_get):
            runner.invoke(app, ["login", "--key", "bad_key_format"])

        assert call_count == 0


class TestLoginRootBaseUrl:
    @respx.mock
    def test_root_base_url_honored_by_login(self, tmp_home: Path) -> None:
        """Root --base-url should be used by login when login's own --base-url is not passed."""
        staging_url = "https://staging-api.onepin.ai/api/v1/auth/whoami"
        respx.get(staging_url).mock(return_value=httpx.Response(200, json=_WHOAMI_RESPONSE))

        result = runner.invoke(
            app,
            ["--base-url", "https://staging-api.onepin.ai", "login", "--key", "op_live_stagekey"],
        )

        assert result.exit_code == 0, result.output
        creds_path = tmp_home / ".onepin" / "credentials"
        content = creds_path.read_text()
        assert "https://staging-api.onepin.ai" in content

    @respx.mock
    def test_login_local_base_url_wins_over_root(self, tmp_home: Path) -> None:
        """Login's own --base-url takes precedence over root --base-url."""
        local_url = "https://local-api.onepin.ai/api/v1/auth/whoami"
        respx.get(local_url).mock(return_value=httpx.Response(200, json=_WHOAMI_RESPONSE))

        result = runner.invoke(
            app,
            [
                "--base-url",
                "https://root-api.onepin.ai",
                "login",
                "--key",
                "op_live_localkey",
                "--base-url",
                "https://local-api.onepin.ai",
            ],
        )

        assert result.exit_code == 0, result.output
        creds_path = tmp_home / ".onepin" / "credentials"
        content = creds_path.read_text()
        assert "https://local-api.onepin.ai" in content


class TestLoginErrors:
    @respx.mock
    def test_401_exits_1_with_invalid_api_key_message(self, tmp_home: Path) -> None:
        """401 from /whoami → exits 1, prints [INVALID_API_KEY] and dashboard URL."""
        respx.get(_WHOAMI_URL).mock(
            return_value=httpx.Response(
                401,
                json={"error": {"code": "INVALID_API_KEY", "message": "Key rejected"}, "meta": {}},
            )
        )

        result = runner.invoke(app, ["login", "--key", "op_live_badkey"])

        assert result.exit_code == 1
        assert "INVALID_API_KEY" in result.output
        assert "app.onepin.ai/workspace/~/settings/api" in result.output

    @respx.mock
    def test_network_error_exits_1_with_network_error_message(self, tmp_home: Path) -> None:
        """ConnectError → exits 1, prints [NETWORK_ERROR]."""
        respx.get(_WHOAMI_URL).mock(side_effect=httpx.ConnectError("refused"))

        result = runner.invoke(app, ["login", "--key", "op_live_netfail"])

        assert result.exit_code == 1
        assert "NETWORK_ERROR" in result.output
        assert "api.onepin.ai" in result.output
