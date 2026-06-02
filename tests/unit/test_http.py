"""Unit tests for the raw-httpx auth helper (_http.py): verbose logging + error paths."""

from __future__ import annotations

import httpx
import pytest
import respx

from onepin._cli._http import OnePinAuthError, OnePinHTTPError, OnePinNetworkError, _call_whoami

_URL = "https://api.onepin.ai/api/v1/auth/whoami"
_OK = {"data": {"workspace_id": "ws-1", "scopes": ["read"]}, "meta": {"request_id": "r1"}}


class TestCallWhoami:
    @respx.mock
    def test_verbose_logs_to_stderr(self, capsys: pytest.CaptureFixture) -> None:
        respx.get(_URL).mock(return_value=httpx.Response(200, json=_OK))
        data = _call_whoami("op_live_x", "https://api.onepin.ai", verbose=True)
        assert data["workspace_id"] == "ws-1"
        err = capsys.readouterr().err
        assert "GET" in err
        assert "200" in err

    @respx.mock
    def test_network_error(self) -> None:
        respx.get(_URL).mock(side_effect=httpx.ConnectError("down"))
        with pytest.raises(OnePinNetworkError):
            _call_whoami("op_live_x", "https://api.onepin.ai")

    @respx.mock
    def test_401_is_auth_error(self) -> None:
        body = {"error": {"code": "INVALID_API_KEY", "message": "bad"}, "meta": {"request_id": "r2"}}
        respx.get(_URL).mock(return_value=httpx.Response(401, json=body))
        with pytest.raises(OnePinAuthError) as exc:
            _call_whoami("op_live_x", "https://api.onepin.ai")
        assert exc.value.request_id == "r2"

    @respx.mock
    def test_500_is_http_error(self) -> None:
        body = {"error": {"code": "SERVER_ERROR", "message": "boom"}}
        respx.get(_URL).mock(return_value=httpx.Response(500, json=body))
        with pytest.raises(OnePinHTTPError) as exc:
            _call_whoami("op_live_x", "https://api.onepin.ai")
        assert exc.value.error_code == "SERVER_ERROR"
