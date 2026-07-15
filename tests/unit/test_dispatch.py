"""Unit tests for the dispatcher's transforms, unwrap modes, and synthesis (the SPOF)."""

from __future__ import annotations

import datetime as dt
import enum
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from onepin._cli import _dispatch
from onepin._cli._ctx import CliError
from onepin._cli._spec import Cmd, Opt


class TestMethodResolution:
    def test_resolves_canonical_path(self) -> None:
        canonical = object()
        client = SimpleNamespace(workflows=SimpleNamespace(runs=SimpleNamespace(steps=canonical)))

        assert _dispatch._resolve_method(client, ("workflows.runs.steps",)) is canonical

    def test_falls_back_when_canonical_path_is_absent(self) -> None:
        legacy = object()
        client = SimpleNamespace(workflows=SimpleNamespace(get_run_steps=legacy))

        resolved = _dispatch._resolve_method(
            client,
            ("workflows.runs.steps", "workflows.get_run_steps"),
        )

        assert resolved is legacy

    def test_prefers_canonical_path_when_both_exist(self) -> None:
        canonical = object()
        legacy = object()
        client = SimpleNamespace(
            workflows=SimpleNamespace(
                runs=SimpleNamespace(steps=canonical),
                get_run_steps=legacy,
            )
        )

        resolved = _dispatch._resolve_method(
            client,
            ("workflows.runs.steps", "workflows.get_run_steps"),
        )

        assert resolved is canonical

    def test_reports_all_attempted_paths_when_none_resolve(self) -> None:
        client = SimpleNamespace(workflows=SimpleNamespace())

        with pytest.raises(AttributeError) as exc_info:
            _dispatch._resolve_method(
                client,
                ("workflows.runs.steps", "workflows.get_run_steps"),
            )

        message = str(exc_info.value)
        assert "workflows.runs.steps" in message
        assert "workflows.get_run_steps" in message


class TestTransforms:
    def test_wrap_list(self) -> None:
        opt = Opt("--sort", ("name",), None, transform="wrap_list")
        assert _dispatch._apply_transform(opt, "name") == ["name"]

    def test_comma_list(self) -> None:
        opt = Opt("--language", "str", None, transform="comma_list")
        assert _dispatch._apply_transform(opt, "en-us, ko-kr ,") == ["en-us", "ko-kr"]

    def test_datetime(self) -> None:
        opt = Opt("--from", "datetime", None, transform="datetime")
        result = _dispatch._apply_transform(opt, "2025-01-01T00:00:00Z")
        assert isinstance(result, dt.datetime)
        assert result.tzinfo is not None

    def test_datetime_invalid_raises_clierror(self) -> None:
        opt = Opt("--from", "datetime", None, transform="datetime")
        with pytest.raises(CliError) as exc:
            _dispatch._apply_transform(opt, "not-a-date")
        assert exc.value.code == "INVALID_DATETIME"

    def test_none_passes_through(self) -> None:
        opt = Opt("--sort", ("name",), None, transform="wrap_list")
        assert _dispatch._apply_transform(opt, None) is None

    def test_enum_member_coerced_to_value(self) -> None:
        choice = enum.Enum("C", {"A": "a", "B": "b"}, type=str)
        opt = Opt("--x", ("a", "b"), None)
        assert _dispatch._apply_transform(opt, choice.A) == "a"

    def test_provider_key_request_bare_string(self) -> None:
        opt = Opt("--key", "str", None, transform="provider_key_request")
        assert _dispatch._apply_transform(opt, "sk-123") == {"api_key": "sk-123"}

    def test_provider_key_request_inline_json(self) -> None:
        opt = Opt("--key", "str", None, transform="provider_key_request")
        assert _dispatch._apply_transform(opt, '{"token": "abc"}') == {"token": "abc"}

    def test_provider_key_request_bad_json_raises(self) -> None:
        opt = Opt("--key", "str", None, transform="provider_key_request")
        with pytest.raises(CliError) as exc:
            _dispatch._apply_transform(opt, "{not json")
        assert exc.value.code == "INVALID_JSON"

    def test_unknown_transform_raises(self) -> None:
        opt = Opt("--x", "str", None, transform="bogus")
        with pytest.raises(CliError):
            _dispatch._apply_transform(opt, "v")


class TestJsonFile:
    def test_inline_json_definition(self) -> None:
        payload = {"graph": {"nodes": [], "edges": []}, "execution": {}}
        model = _dispatch._load_definition(json.dumps(payload))
        assert hasattr(model, "graph")

    def test_at_path_definition(self, tmp_path: Path) -> None:
        f = tmp_path / "def.json"
        f.write_text(json.dumps({"graph": {"nodes": [], "edges": []}, "execution": {}}))
        model = _dispatch._load_definition(f"@{f}")
        assert hasattr(model, "graph")

    def test_missing_file_raises_filenotfound(self) -> None:
        with pytest.raises(FileNotFoundError):
            _dispatch._load_definition("@/nonexistent/def.json")

    def test_bad_json_raises_jsondecode(self, tmp_path: Path) -> None:
        f = tmp_path / "bad.json"
        f.write_text("{not valid")
        with pytest.raises(json.JSONDecodeError):
            _dispatch._load_definition(f"@{f}")

    def test_bad_shape_raises_validationerror(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            _dispatch._load_definition('{"graph": "should-be-object"}')


class TestBuildKwargs:
    def test_dest_rename_and_const_inject(self) -> None:
        cmd = Cmd(
            "uploads",
            "confirm",
            "uploads.confirm",
            "x",
            args=[("upload_id", "")],
            options=[Opt("--workflow-id", "str", None, dest="context_id", required=True)],
            consts={"context_type": "workflow"},
        )
        bound = {"upload_id": "u1", "context_id": "wf1"}
        positional, kwargs = _dispatch._build_kwargs(cmd, bound)
        assert positional == ["u1"]
        assert kwargs == {"context_type": "workflow", "context_id": "wf1"}

    def test_none_option_dropped(self) -> None:
        cmd = Cmd("workflows", "list", "workflows.list", "x", options=[Opt("--search", "str", None)])
        _, kwargs = _dispatch._build_kwargs(cmd, {"search": None})
        assert "search" not in kwargs

    def test_local_flags_not_forwarded(self) -> None:
        cmd = Cmd(
            "provider-keys",
            "list",
            "provider_keys.list_provider_keys",
            "x",
            options=[Opt("--json", "bool", False, dest="json_output_local")],
        )
        _, kwargs = _dispatch._build_kwargs(cmd, {"json_output_local": True})
        assert kwargs == {}

    def test_bool_filter_at_default_not_forwarded(self) -> None:
        cmd = Cmd(
            "templates",
            "list",
            "templates.list",
            "x",
            options=[Opt("--favorites-only", "bool", False, help="Only favorites.")],
        )
        _, kwargs = _dispatch._build_kwargs(cmd, {"favorites_only": False})
        assert "favorites_only" not in kwargs

    def test_bool_filter_true_forwarded(self) -> None:
        cmd = Cmd(
            "templates",
            "list",
            "templates.list",
            "x",
            options=[Opt("--favorites-only", "bool", False, help="Only favorites.")],
        )
        _, kwargs = _dispatch._build_kwargs(cmd, {"favorites_only": True})
        assert kwargs["favorites_only"] is True


class TestConditionalWorkspace:
    def test_keyword_only_workspace_id_accepted(self) -> None:
        def with_ws(workflow_id, *, workspace_id=None):
            return None

        assert _dispatch._accepts_workspace_kwarg(with_ws) is True

    def test_positional_workspace_id_rejected(self) -> None:
        # A path param named workspace_id (positional) must NOT receive the root --workspace.
        def positional_ws(workspace_id, *, request_options=None):
            return None

        assert _dispatch._accepts_workspace_kwarg(positional_ws) is False

    def test_no_workspace_param_rejected(self) -> None:
        def no_ws(ws_id):
            return None

        assert _dispatch._accepts_workspace_kwarg(no_ws) is False


class TestRedaction:
    def test_masks_secret_fields(self) -> None:
        out = _dispatch._redact({"api_key": "sk-abcdef1234", "name": "ok"})
        assert out["api_key"] == "****1234"
        assert out["name"] == "ok"

    def test_short_secret_fully_masked(self) -> None:
        assert _dispatch._redact({"token": "abc"})["token"] == "****"

    def test_nested_redaction(self) -> None:
        out = _dispatch._redact({"providers": [{"secret": "longsecret9999"}]})
        assert out["providers"][0]["secret"] == "****9999"

    def test_mask_helper(self) -> None:
        assert _dispatch._mask("0123456789") == "****6789"
        assert _dispatch._mask("ab") == "****"


class TestColumns:
    def test_declared_columns_win(self) -> None:
        cmd = Cmd("g", "n", "m", "x", columns=["a", "b"])
        assert _dispatch._columns_for(cmd, [{"a": 1, "b": 2, "c": 3}]) == ["a", "b"]

    def test_fallback_to_first_row_keys(self) -> None:
        cmd = Cmd("g", "n", "m", "x", columns=[])
        assert _dispatch._columns_for(cmd, [{"x": 1, "y": 2}]) == ["x", "y"]


class TestFormatMapSafety:
    def test_missing_key_returns_empty_string(self) -> None:
        ctx = _dispatch._fmt_context({}, {})
        # Template referencing an absent key must not raise.
        result = "hello {nonexistent} world".format_map(ctx)
        assert result == "hello  world"

    def test_present_keys_substituted(self) -> None:
        ctx = _dispatch._fmt_context({"id": "wf-1"}, {"workflow_id": "wf-1"})
        result = "Deleted {workflow_id}, id={id}".format_map(ctx)
        assert result == "Deleted wf-1, id=wf-1"


class TestSynthesizedCommandValidity:
    """Every TABLE row + composite must synthesize into a Typer-valid command tree."""

    def test_all_commands_build_and_render_help(self) -> None:
        import typer
        from typer.testing import CliRunner

        from onepin._cli.main import app

        runner = CliRunner()
        cli = typer.main.get_command(app)
        # Building the command tree must not raise.
        assert cli is not None
        # Root help renders cleanly.
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    @pytest.mark.parametrize(
        "argv",
        [
            ["workflows", "list", "--help"],
            ["workflows", "delete", "--help"],
            ["workflows", "runs", "list", "--help"],
            ["templates", "create", "--help"],
            ["voices", "list", "--help"],
            ["nodes", "list", "--help"],
            ["workspace", "members", "invite", "--help"],
            ["usage", "summary", "--help"],
        ],
    )
    def test_command_help_renders(self, argv: list[str]) -> None:
        from typer.testing import CliRunner

        from onepin._cli.main import app

        result = CliRunner().invoke(app, argv)
        assert result.exit_code == 0, result.output
