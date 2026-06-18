"""CLI tests for `onepin health` (version/status surface) and the required-version gate.

Uses respx so the real Fern request/response path and the version-gate response hook both run.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from typer.testing import CliRunner

from onepin._cli import _update_check as uc
from onepin._cli.main import app

runner = CliRunner()
_BASE = "https://api.onepin.ai"


def _invoke(argv: list[str]):
    return runner.invoke(app, ["--api-key", "op_live_x", "--base-url", _BASE, *argv])


@pytest.fixture(autouse=True)
def _fixed_sdk_version(monkeypatch: pytest.MonkeyPatch) -> None:
    # Pin the version shown as "SDK version" so assertions are stable.
    monkeypatch.setattr("onepin._cli.commands.health.__version__", "0.6.0")


def _seed_recommended(version: str) -> None:
    path = uc._cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"UPGRADE_AVAILABLE 0.6.0 {version}\n", encoding="utf-8")


class TestHealthLive:
    @respx.mock
    def test_human_full_surface(self, tmp_home) -> None:
        _seed_recommended("0.9.0")
        respx.get(f"{_BASE}/health").mock(
            return_value=httpx.Response(
                200,
                json={"status": "ok", "version": "0.34.3"},
                headers={"X-OnePin-Required-Version": "0.1.0"},
            )
        )
        result = _invoke(["health", "live"])
        assert result.exit_code == 0, result.output
        assert "status: ok" in result.output
        assert "SDK version: 0.6.0" in result.output
        assert "API version: 0.34.3" in result.output
        assert "Recommended SDK version: 0.9.0" in result.output
        assert "Required SDK version: 0.1.0" in result.output

    @respx.mock
    def test_json(self, tmp_home) -> None:
        _seed_recommended("0.9.0")
        respx.get(f"{_BASE}/health").mock(
            return_value=httpx.Response(
                200,
                json={"status": "ok", "version": "0.34.3"},
                headers={"X-OnePin-Required-Version": "0.1.0"},
            )
        )
        result = _invoke(["health", "live", "--json"])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["status"] == "ok"
        assert payload["sdk_version"] == "0.6.0"
        assert payload["api_version"] == "0.34.3"
        assert payload["recommended_version"] == "0.9.0"
        assert payload["required_version"] == "0.1.0"

    @respx.mock
    def test_unknown_sources(self, tmp_home) -> None:
        # No version field in the body, no required header, no cached recommended.
        respx.get(f"{_BASE}/health").mock(return_value=httpx.Response(200, json={}))
        result = _invoke(["health", "live"])
        assert result.exit_code == 0, result.output
        assert "status: ok" in result.output  # synthesized on a 200
        assert "API version: unknown" in result.output
        assert "Recommended SDK version: unknown" in result.output
        assert "Required SDK version: unknown" in result.output


class TestRequiredGate:
    @respx.mock
    def test_stop_via_header_hook(self, tmp_home) -> None:
        # A floor above any real installed version trips the client-side response hook.
        respx.get(f"{_BASE}/health").mock(
            return_value=httpx.Response(200, json={"status": "ok"}, headers={"X-OnePin-Required-Version": "999.0.0"})
        )
        result = _invoke(["health", "live"])
        assert result.exit_code == 1
        assert "999.0.0" in result.output
        assert "pip install --upgrade" in result.output

    @respx.mock
    def test_stop_json_envelope(self, tmp_home) -> None:
        # --json upgrade failures emit the structured error envelope (UPGRADE_REQUIRED).
        respx.get(f"{_BASE}/health").mock(
            return_value=httpx.Response(200, json={}, headers={"X-OnePin-Required-Version": "999.0.0"})
        )
        result = runner.invoke(app, ["--api-key", "op_live_x", "--base-url", _BASE, "--json", "health", "live"])
        assert result.exit_code == 1
        assert '"code": "UPGRADE_REQUIRED"' in result.output

    @respx.mock
    def test_stop_via_server_426(self, tmp_home) -> None:
        respx.get(f"{_BASE}/health").mock(
            return_value=httpx.Response(
                426,
                json={"error": {"code": "sdk_upgrade_required", "required_version": "9.9.9"}},
            )
        )
        result = _invoke(["health", "live"])
        assert result.exit_code == 1
        assert "9.9.9" in result.output
        assert "pip install --upgrade" in result.output


class TestHealthReady:
    @respx.mock
    def test_human(self, tmp_home) -> None:
        respx.get(f"{_BASE}/ready").mock(return_value=httpx.Response(200, json={"status": "ok"}))
        result = _invoke(["health", "ready"])
        assert result.exit_code == 0, result.output
        assert "status: ok" in result.output
        assert "SDK version: 0.6.0" in result.output


class TestAuthPath426:
    @respx.mock
    def test_whoami_surfaces_upgrade(self, tmp_home) -> None:
        # The raw-httpx auth path must also surface a 426 floor as an upgrade stop.
        respx.get(f"{_BASE}/api/v1/auth/whoami").mock(
            return_value=httpx.Response(
                426, json={"error": {"code": "sdk_upgrade_required", "required_version": "9.9.9"}}
            )
        )
        result = runner.invoke(app, ["--api-key", "op_live_x", "--base-url", _BASE, "whoami"])
        assert result.exit_code == 1
        assert "UPGRADE_REQUIRED" in result.output
        assert "9.9.9" in result.output
        assert "pip install --upgrade" in result.output
