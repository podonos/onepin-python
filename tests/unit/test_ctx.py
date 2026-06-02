"""Unit tests for _ctx helpers: credential resolution, jsonable coercion, error mapping."""

from __future__ import annotations

import datetime as dt

import httpx
import pytest

from onepin._cli import _ctx, _state
from onepin._cli._http import OnePinAuthError, _parse_error_envelope


class TestToJsonable:
    def test_datetime(self) -> None:
        assert _ctx.to_jsonable(dt.datetime(2025, 1, 1)).startswith("2025-01-01")

    def test_nested_containers(self) -> None:
        assert _ctx.to_jsonable({"a": [1, dt.date(2025, 1, 1)]}) == {"a": [1, "2025-01-01"]}

    def test_pydantic_model(self) -> None:
        from onepin.types.meta import Meta

        out = _ctx.to_jsonable(Meta(request_id="r", timestamp=dt.datetime(2025, 1, 1)))
        assert out["request_id"] == "r"

    def test_scalar_passthrough(self) -> None:
        assert _ctx.to_jsonable(5) == 5
        assert _ctx.to_jsonable("x") == "x"


class TestOutputJson:
    def test_local_true(self) -> None:
        _state.root_options = {}
        assert _ctx.output_json(True) is True

    def test_root_true(self) -> None:
        _state.root_options = {"json_output": True}
        assert _ctx.output_json(False) is True

    def test_both_false(self) -> None:
        _state.root_options = {"json_output": False}
        assert _ctx.output_json(False) is False


class TestResolveCliCredentials:
    def test_flag_source(self, monkeypatch) -> None:
        import click

        _state.root_options = {
            "api_key": "op_live_flag",
            "api_key_source": click.core.ParameterSource.COMMANDLINE,
        }
        creds = _ctx.resolve_cli_credentials()
        assert creds.api_key == "op_live_flag"
        assert creds.source == "flag"

    def test_env_not_treated_as_flag(self, monkeypatch) -> None:
        import click

        monkeypatch.setenv("ONEPIN_API_KEY", "op_live_env")
        _state.root_options = {
            "api_key": "op_live_env",
            "api_key_source": click.core.ParameterSource.ENVIRONMENT,
        }
        creds = _ctx.resolve_cli_credentials()
        assert creds.source == "env"


class TestBuildClientLazyImport:
    def test_no_key_raises(self) -> None:
        from onepin._cli.auth.resolver import ResolvedCredentials

        with pytest.raises(OnePinAuthError):
            _ctx.build_client(ResolvedCredentials(api_key=None, base_url=None, source="default"))

    def test_bad_base_url_scheme_raises(self) -> None:
        from onepin._cli.auth.resolver import ResolvedCredentials

        with pytest.raises(OnePinAuthError):
            _ctx.build_client(ResolvedCredentials(api_key="op_live_x", base_url="ftp://x", source="flag"))

    def test_builds_client(self) -> None:
        from onepin._cli.auth.resolver import ResolvedCredentials

        client = _ctx.build_client(ResolvedCredentials(api_key="op_live_x", base_url=None, source="flag"))
        assert client is not None


class TestClassifyApiError:
    def test_envelope_parsed(self) -> None:
        from onepin.core.api_error import ApiError

        exc = ApiError(
            status_code=404, body={"error": {"code": "NOT_FOUND", "message": "gone"}, "meta": {"request_id": "r9"}}
        )
        code, message, rid = _ctx._classify_api_error(exc)
        assert code == "NOT_FOUND"
        assert message == "gone"
        assert rid == "r9"

    def test_status_fallback(self) -> None:
        from onepin.core.api_error import ApiError

        code, message, rid = _ctx._classify_api_error(ApiError(status_code=500, body=None))
        assert code == "SERVER_ERROR"
        assert rid is None


class TestClassifyOtherError:
    def test_connect_error(self) -> None:
        code, _ = _ctx._classify_other_error(httpx.ConnectError("x"))
        assert code == "NETWORK_ERROR"

    def test_timeout(self) -> None:
        code, _ = _ctx._classify_other_error(httpx.ReadTimeout("x"))
        assert code == "TIMEOUT"

    def test_transport_error(self) -> None:
        code, _ = _ctx._classify_other_error(httpx.TransportError("x"))
        assert code == "NETWORK_ERROR"

    def test_json_decode_error(self) -> None:
        import json

        try:
            json.loads("{bad")
        except json.JSONDecodeError as exc:
            code, _ = _ctx._classify_other_error(exc)
            assert code == "INVALID_JSON"

    def test_validation_error(self) -> None:
        from onepin.types import WorkflowDefinitionInput

        try:
            WorkflowDefinitionInput.model_validate({"graph": "nope"})
        except Exception as exc:  # noqa: BLE001
            code, message = _ctx._classify_other_error(exc)
            assert code == "VALIDATION_ERROR"
            assert "Invalid input" in message

    def test_is_a_directory(self) -> None:
        code, _ = _ctx._classify_other_error(IsADirectoryError(21, "is dir", "/tmp"))
        assert code == "FILE_NOT_FOUND"

    def test_file_not_found(self) -> None:
        code, _ = _ctx._classify_other_error(FileNotFoundError(2, "no", "f.txt"))
        assert code == "FILE_NOT_FOUND"

    def test_permission(self) -> None:
        code, _ = _ctx._classify_other_error(PermissionError(13, "denied", "f.txt"))
        assert code == "PERMISSION_DENIED"

    def test_unknown_returns_none(self) -> None:
        code, _ = _ctx._classify_other_error(RuntimeError("weird"))
        assert code is None


class TestStatusMapping:
    def test_none_status(self) -> None:
        assert _ctx._status_code_name(None) == "API_ERROR"
        assert _ctx._status_message(None) == "API request failed."

    def test_known_status(self) -> None:
        assert _ctx._status_code_name(409) == "CONFLICT"

    def test_server_error(self) -> None:
        assert _ctx._status_code_name(503) == "SERVER_ERROR"

    def test_unknown_4xx(self) -> None:
        assert _ctx._status_code_name(418) == "API_ERROR"


class TestApiErrorsNetworkPaths:
    def test_network_error_mapped(self, capsys) -> None:
        with pytest.raises(SystemExit) as exc:
            with _ctx.api_errors(False):
                raise httpx.ConnectError("down")
        assert exc.value.code == 1
        assert "NETWORK_ERROR" in capsys.readouterr().err

    def test_validation_error_mapped_json(self, capsys) -> None:
        from onepin.types import WorkflowDefinitionInput

        with pytest.raises(SystemExit):
            with _ctx.api_errors(True):
                WorkflowDefinitionInput.model_validate({"graph": "nope"})
        assert '"code": "VALIDATION_ERROR"' in capsys.readouterr().err


class TestApiErrorsContextManager:
    def test_clierror_exits_1(self, capsys) -> None:
        with pytest.raises(SystemExit) as exc:
            with _ctx.api_errors(False):
                raise _ctx.CliError("BOOM", "it broke")
        assert exc.value.code == 1
        assert "[BOOM] it broke" in capsys.readouterr().err

    def test_clierror_json_envelope(self, capsys) -> None:
        with pytest.raises(SystemExit):
            with _ctx.api_errors(True):
                raise _ctx.CliError("BOOM", "it broke", request_id="r1")
        err = capsys.readouterr().err
        assert '"code": "BOOM"' in err
        assert '"request_id": "r1"' in err

    def test_keyboard_interrupt_exits_130(self) -> None:
        with pytest.raises(SystemExit) as exc:
            with _ctx.api_errors(False):
                raise KeyboardInterrupt()
        assert exc.value.code == 130

    def test_broken_pipe_exits_0(self) -> None:
        with pytest.raises(SystemExit) as exc:
            with _ctx.api_errors(False):
                raise BrokenPipeError()
        assert exc.value.code == 0

    def test_unknown_exception_reraised(self) -> None:
        with pytest.raises(RuntimeError):
            with _ctx.api_errors(False):
                raise RuntimeError("not mapped")


class TestParseErrorEnvelope:
    def test_dict_envelope(self) -> None:
        out = _parse_error_envelope({"error": {"code": "X", "message": "m"}, "meta": {"request_id": "r"}})
        assert out == {"code": "X", "message": "m", "request_id": "r"}

    def test_string_json(self) -> None:
        out = _parse_error_envelope('{"error": {"code": "Y"}}')
        assert out["code"] == "Y"

    def test_string_opaque(self) -> None:
        assert _parse_error_envelope("just a message") == {"message": "just a message"}

    def test_none(self) -> None:
        assert _parse_error_envelope(None) == {}

    def test_flat_detail(self) -> None:
        out = _parse_error_envelope({"detail": "boom"})
        assert out["message"] == "boom"


class TestParsingErrorMapped:
    """Fern ParsingError (malformed 2xx body) must be caught and mapped to INVALID_RESPONSE."""

    def test_parsing_error_plain(self, capsys) -> None:
        from onepin.core.parse_error import ParsingError

        with pytest.raises(SystemExit) as exc:
            with _ctx.api_errors(False):
                raise ParsingError(status_code=200, body="<html>not json</html>")
        assert exc.value.code == 1
        assert "[INVALID_RESPONSE]" in capsys.readouterr().err

    def test_parsing_error_json_envelope(self, capsys) -> None:
        from onepin.core.parse_error import ParsingError

        with pytest.raises(SystemExit) as exc:
            with _ctx.api_errors(True):
                raise ParsingError(status_code=200, body="garbage")
        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert '"code": "INVALID_RESPONSE"' in err
        # Must NOT leak raw response body internals.
        assert "garbage" not in err
