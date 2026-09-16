"""Tests for hand-written composite commands: run/watch, uploads create, downloads, schemas."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import httpx
import pytest
import respx
from typer.testing import CliRunner

from onepin._cli._ctx import CliError
from onepin._cli.commands import composites
from onepin._cli.main import app

runner = CliRunner()
NOW = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)


def _meta():
    from onepin.types.meta import Meta

    return Meta(request_id="r1", timestamp=NOW)


def _run_out(status: str, run_id: str = "run-1"):
    from onepin.types import ApiResponseWorkflowRunOut, WorkflowRunOut

    run = WorkflowRunOut(
        id=run_id,
        workflow_id="wf-1",
        status=status,
        run_number=1,
        total_nodes=1,
        total_steps=1,
        finished_steps=1,
        token_cost=0,
        usage_summary=None,
        started_at=NOW,
        completed_at=None,
        created_at=NOW,
        updated_at=NOW,
        error=None,
        has_export=False,
        triggered_by=None,
    )
    return ApiResponseWorkflowRunOut(data=run, meta=_meta())


_META_JSON = {"request_id": "01JTEST00000000000000000000", "timestamp": "2025-01-01T00:00:00Z"}

_RUN_JSON = {
    "id": "run-1",
    "workflow_id": "wf-1",
    "status": "running",
    "run_number": 1,
    "total_nodes": 1,
    "total_steps": 1,
    "finished_steps": 0,
    "token_cost": 0,
    "usage_summary": None,
    "started_at": "2025-01-01T00:00:00Z",
    "completed_at": None,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
    "error": None,
    "has_export": False,
    "triggered_by": None,
}


# === workflows run [--watch] =============================================================


class _Runs:
    def __init__(self, statuses: list[str]) -> None:
        self._statuses = statuses
        self._i = 0
        self.start_kwargs: dict | None = None

    def start(self, workflow_id, **kw):
        self.start_kwargs = kw
        return _run_out(self._statuses[0])

    def status(self, workflow_id, run_id, **kw):
        self._i = min(self._i + 1, len(self._statuses) - 1)
        return _run_out(self._statuses[self._i], run_id)


class _WfClient:
    def __init__(self, statuses: list[str]) -> None:
        self.workflows = type("W", (), {"runs": _Runs(statuses)})()


@pytest.fixture
def patch_client(monkeypatch: pytest.MonkeyPatch):
    def _apply(client):
        monkeypatch.setattr(composites, "get_client", lambda: client)

    return _apply


class TestWorkflowRun:
    def test_no_watch_prints_started(self, patch_client, tmp_home) -> None:
        patch_client(_WfClient(["running"]))
        result = runner.invoke(app, ["--api-key", "op_live_x", "workflows", "run", "wf-1"])
        assert result.exit_code == 0, result.output
        assert "Started run run-1" in result.output

    def test_watch_to_terminal_completed(self, patch_client, monkeypatch, tmp_home) -> None:
        monkeypatch.setattr(composites.time, "sleep", lambda s: None)
        patch_client(_WfClient(["running", "running", "completed"]))
        result = runner.invoke(
            app, ["--api-key", "op_live_x", "workflows", "run", "wf-1", "--watch", "--timeout", "30"]
        )
        assert result.exit_code == 0, result.output
        assert "finished: completed" in result.output

    def test_watch_failed_exits_1(self, patch_client, monkeypatch, tmp_home) -> None:
        monkeypatch.setattr(composites.time, "sleep", lambda s: None)
        patch_client(_WfClient(["running", "failed"]))
        result = runner.invoke(app, ["--api-key", "op_live_x", "workflows", "run", "wf-1", "--watch"])
        assert result.exit_code == 1
        assert "finished: failed" in result.output

    def test_watch_timeout_exits_1(self, patch_client, monkeypatch, tmp_home) -> None:
        monkeypatch.setattr(composites.time, "sleep", lambda s: None)
        # never terminal; timeout 0 forces the deadline immediately
        patch_client(_WfClient(["running"]))
        result = runner.invoke(app, ["--api-key", "op_live_x", "workflows", "run", "wf-1", "--watch", "--timeout", "0"])
        assert result.exit_code == 1
        assert "Timed out" in result.output

    def test_script_flags_ride_as_body_params(self, patch_client, tmp_home) -> None:
        client = _WfClient(["running"])
        patch_client(client)
        result = runner.invoke(
            app,
            [
                "--api-key",
                "op_live_x",
                "workflows",
                "run",
                "wf-1",
                "--script",
                "Hello world!",
                "--source-language",
                "en-us",
            ],
        )
        assert result.exit_code == 0, result.output
        assert client.workflows.runs.start_kwargs["request_options"] == {
            "additional_body_parameters": {"script_text": "Hello world!", "source_language": "en-us"}
        }

    def test_script_flag_alone_sends_only_script_text(self, patch_client, tmp_home) -> None:
        client = _WfClient(["running"])
        patch_client(client)
        result = runner.invoke(app, ["--api-key", "op_live_x", "workflows", "run", "wf-1", "--script", "Hi"])
        assert result.exit_code == 0, result.output
        assert client.workflows.runs.start_kwargs["request_options"] == {
            "additional_body_parameters": {"script_text": "Hi"}
        }

    def test_no_script_flags_sends_no_request_options(self, patch_client, tmp_home) -> None:
        client = _WfClient(["running"])
        patch_client(client)
        result = runner.invoke(app, ["--api-key", "op_live_x", "workflows", "run", "wf-1"])
        assert result.exit_code == 0, result.output
        assert "request_options" not in client.workflows.runs.start_kwargs


# === workflows preview-run ===============================================================


_ESTIMATE = {
    "min_credits": 107,
    "expected_credits": 107,
    "max_credits": 214,
    "breakdown": [],
    "current_balance": 5000,
    "deficit_at_max": 0,
    "can_run": True,
}


class TestWorkflowPreviewRun:
    """The estimate must price the body the run will actually send (see _run_scoped_body)."""

    @respx.mock
    def test_script_rides_in_the_body(self, tmp_home) -> None:
        route = respx.post("https://api.onepin.ai/api/v1/workflows/wf-1/runs/preview").mock(
            return_value=httpx.Response(200, json={"data": _ESTIMATE, "meta": _META_JSON})
        )
        result = runner.invoke(
            app,
            ["--api-key", "op_live_x", "workflows", "preview-run", "wf-1", "--script", "Hi", "--json"],
        )
        assert result.exit_code == 0, result.output
        assert json.loads(route.calls[0].request.content) == {"script_text": "Hi"}
        assert '"expected_credits": 107' in result.output

    @respx.mock
    def test_body_matches_the_run_byte_for_byte(self, tmp_home) -> None:
        """A cost quoted from a different body than the one charged is the bug being prevented."""
        preview = respx.post("https://api.onepin.ai/api/v1/workflows/wf-1/runs/preview").mock(
            return_value=httpx.Response(200, json={"data": _ESTIMATE, "meta": _META_JSON})
        )
        run = respx.post("https://api.onepin.ai/api/v1/workflows/wf-1/runs").mock(
            return_value=httpx.Response(202, json={"data": _RUN_JSON, "meta": _META_JSON})
        )
        argv = ["--script", "Hello world!", "--source-language", "en-us"]
        assert runner.invoke(app, ["--api-key", "op_live_x", "workflows", "preview-run", "wf-1", *argv]).exit_code == 0
        assert runner.invoke(app, ["--api-key", "op_live_x", "workflows", "run", "wf-1", *argv]).exit_code == 0
        assert preview.calls[0].request.content == run.calls[0].request.content

    @respx.mock
    def test_no_overrides_sends_no_body(self, tmp_home) -> None:
        route = respx.post("https://api.onepin.ai/api/v1/workflows/wf-1/runs/preview").mock(
            return_value=httpx.Response(200, json={"data": _ESTIMATE, "meta": _META_JSON})
        )
        result = runner.invoke(app, ["--api-key", "op_live_x", "workflows", "preview-run", "wf-1", "--json"])
        assert result.exit_code == 0, result.output
        assert route.calls[0].request.content == b""

    @respx.mock
    def test_text_output_renders_the_credits(self, tmp_home) -> None:
        respx.post("https://api.onepin.ai/api/v1/workflows/wf-1/runs/preview").mock(
            return_value=httpx.Response(200, json={"data": _ESTIMATE, "meta": _META_JSON})
        )
        result = runner.invoke(app, ["--api-key", "op_live_x", "--no-color", "workflows", "preview-run", "wf-1"])
        assert result.exit_code == 0, result.output
        assert "expected_credits: 107" in result.output

    @respx.mock
    def test_validation_error_exits_1(self, tmp_home) -> None:
        respx.post("https://api.onepin.ai/api/v1/workflows/wf-1/runs/preview").mock(
            return_value=httpx.Response(
                422, json={"error": {"code": "VALIDATION_ERROR", "message": "needs a few fixes"}}
            )
        )
        result = runner.invoke(app, ["--api-key", "op_live_x", "workflows", "preview-run", "wf-1"])
        assert result.exit_code == 1
        assert "VALIDATION_ERROR" in result.output


# === uploads create ======================================================================


class _UploadsClient:
    class uploads:  # noqa: N801
        @staticmethod
        def create(filename, category, **kw):
            from onepin.types import ApiResponseUploadCreateResponse, UploadCreateResponse, UploadOut

            upload = UploadOut(
                id="upl-1",
                user_id="u",
                workspace_id=None,
                filename=filename,
                category=category,
                content_type="text/plain",
                format=None,
                status="pending",
                size_bytes=10,
                download_url=None,
                context_type=None,
                context_id=None,
                created_at=NOW,
                updated_at=NOW,
            )
            data = UploadCreateResponse(upload=upload, upload_url="https://s3.example.com/put?sig=x")
            return ApiResponseUploadCreateResponse(data=data, meta=_meta())


class TestUploadCreate:
    @respx.mock
    def test_happy(self, monkeypatch, tmp_home, tmp_path: Path) -> None:
        monkeypatch.setattr(composites, "get_client", lambda: _UploadsClient())
        respx.put("https://s3.example.com/put").mock(return_value=httpx.Response(200))
        f = tmp_path / "script.txt"
        f.write_text("hello")
        result = runner.invoke(
            app, ["--api-key", "op_live_x", "uploads", "create", "--file", str(f), "--category", "script"]
        )
        assert result.exit_code == 0, result.output
        assert "upl-1" in result.output

    def test_missing_file(self, monkeypatch, tmp_home) -> None:
        monkeypatch.setattr(composites, "get_client", lambda: _UploadsClient())
        result = runner.invoke(
            app, ["--api-key", "op_live_x", "uploads", "create", "--file", "/no/such.txt", "--category", "script"]
        )
        assert result.exit_code == 1
        assert "FILE_NOT_FOUND" in result.output

    def test_bad_category(self, tmp_home, tmp_path: Path) -> None:
        f = tmp_path / "x.txt"
        f.write_text("x")
        result = runner.invoke(
            app, ["--api-key", "op_live_x", "uploads", "create", "--file", str(f), "--category", "bogus"]
        )
        assert result.exit_code == 1
        assert "INVALID_CATEGORY" in result.output

    @respx.mock
    def test_s3_rejects_upload(self, monkeypatch, tmp_home, tmp_path: Path) -> None:
        monkeypatch.setattr(composites, "get_client", lambda: _UploadsClient())
        respx.put("https://s3.example.com/put").mock(return_value=httpx.Response(403))
        f = tmp_path / "script.txt"
        f.write_text("hello")
        result = runner.invoke(
            app, ["--api-key", "op_live_x", "uploads", "create", "--file", str(f), "--category", "script"]
        )
        assert result.exit_code == 1
        assert "UPLOAD_FAILED" in result.output


# === downloads ===========================================================================


class _DownloadClient:
    class workflows:  # noqa: N801
        @staticmethod
        def download_run(workflow_id, run_id, **kw):
            from onepin.types import ApiResponseDownloadUrlOut, DownloadUrlOut

            return ApiResponseDownloadUrlOut(
                data=DownloadUrlOut(url="https://s3.example.com/get?sig=x", filename="out.zip", expires_at=NOW),
                meta=_meta(),
            )


class TestDownload:
    @respx.mock
    def test_atomic_write(self, monkeypatch, tmp_home, tmp_path: Path) -> None:
        monkeypatch.setattr(composites, "get_client", lambda: _DownloadClient())
        respx.get("https://s3.example.com/get").mock(return_value=httpx.Response(200, content=b"PAYLOAD"))
        out = tmp_path / "out.zip"
        result = runner.invoke(
            app, ["--api-key", "op_live_x", "workflows", "runs", "download", "wf-1", "run-1", "--out", str(out)]
        )
        assert result.exit_code == 0, result.output
        assert out.read_bytes() == b"PAYLOAD"

    @respx.mock
    def test_refuses_clobber_without_force(self, monkeypatch, tmp_home, tmp_path: Path) -> None:
        monkeypatch.setattr(composites, "get_client", lambda: _DownloadClient())
        out = tmp_path / "out.zip"
        out.write_bytes(b"OLD")
        result = runner.invoke(
            app, ["--api-key", "op_live_x", "workflows", "runs", "download", "wf-1", "run-1", "--out", str(out)]
        )
        assert result.exit_code == 1
        assert "FILE_EXISTS" in result.output
        assert out.read_bytes() == b"OLD"

    @respx.mock
    def test_force_overwrites(self, monkeypatch, tmp_home, tmp_path: Path) -> None:
        monkeypatch.setattr(composites, "get_client", lambda: _DownloadClient())
        respx.get("https://s3.example.com/get").mock(return_value=httpx.Response(200, content=b"NEW"))
        out = tmp_path / "out.zip"
        out.write_bytes(b"OLD")
        result = runner.invoke(
            app,
            ["--api-key", "op_live_x", "workflows", "runs", "download", "wf-1", "run-1", "--out", str(out), "--force"],
        )
        assert result.exit_code == 0, result.output
        assert out.read_bytes() == b"NEW"

    @respx.mock
    def test_download_json(self, monkeypatch, tmp_home, tmp_path: Path) -> None:
        monkeypatch.setattr(composites, "get_client", lambda: _DownloadClient())
        respx.get("https://s3.example.com/get").mock(return_value=httpx.Response(200, content=b"DATA"))
        out = tmp_path / "out.zip"
        result = runner.invoke(
            app,
            ["--api-key", "op_live_x", "workflows", "runs", "download", "wf-1", "run-1", "--out", str(out), "--json"],
        )
        assert result.exit_code == 0, result.output
        assert '"ok": true' in result.output
        assert '"path"' in result.output


class TestWorkflowRunJson:
    def test_no_watch_json(self, patch_client, tmp_home) -> None:
        patch_client(_WfClient(["running"]))
        result = runner.invoke(app, ["--api-key", "op_live_x", "workflows", "run", "wf-1", "--json"])
        assert result.exit_code == 0, result.output
        assert '"id": "run-1"' in result.output

    def test_watch_completed_json(self, patch_client, monkeypatch, tmp_home) -> None:
        monkeypatch.setattr(composites.time, "sleep", lambda s: None)
        patch_client(_WfClient(["running", "completed"]))
        result = runner.invoke(app, ["--api-key", "op_live_x", "workflows", "run", "wf-1", "--watch", "--json"])
        assert result.exit_code == 0, result.output
        assert '"status": "completed"' in result.output

    def test_watch_timeout_json_emits_error_envelope(self, patch_client, monkeypatch, tmp_home) -> None:
        monkeypatch.setattr(composites.time, "sleep", lambda s: None)
        patch_client(_WfClient(["running"]))
        result = runner.invoke(
            app,
            ["--api-key", "op_live_x", "workflows", "run", "wf-1", "--watch", "--timeout", "0", "--json"],
        )
        assert result.exit_code == 1
        # CliRunner mixes stdout/stderr; check the structured error envelope is present.
        assert "TIMEOUT" in result.output
        assert "last_status" in result.output


class TestUploadCreateJson:
    @respx.mock
    def test_upload_json(self, monkeypatch, tmp_home, tmp_path: Path) -> None:
        monkeypatch.setattr(composites, "get_client", lambda: _UploadsClient())
        respx.put("https://s3.example.com/put").mock(return_value=httpx.Response(200))
        f = tmp_path / "script.txt"
        f.write_text("hello")
        result = runner.invoke(
            app,
            ["--api-key", "op_live_x", "uploads", "create", "--file", str(f), "--category", "script", "--json"],
        )
        assert result.exit_code == 0, result.output
        assert '"ok": true' in result.output

    @respx.mock
    def test_upload_connection_error(self, monkeypatch, tmp_home, tmp_path: Path) -> None:
        monkeypatch.setattr(composites, "get_client", lambda: _UploadsClient())
        respx.put("https://s3.example.com/put").mock(side_effect=httpx.ConnectError("down"))
        f = tmp_path / "script.txt"
        f.write_text("hello")
        result = runner.invoke(
            app, ["--api-key", "op_live_x", "uploads", "create", "--file", str(f), "--category", "script"]
        )
        assert result.exit_code == 1
        assert "UPLOAD_FAILED" in result.output


# === workflows set-voice =================================================================


def _generator_definition(voice_map=None, node_id="gen-1", extra_generator=False):
    nodes = [
        {"id": "src-1", "type": "source_script", "position": {"x": 0, "y": 0}, "config": {"text": "hi"}},
        {
            "id": node_id,
            "type": "operator_generator",
            "position": {"x": 1, "y": 0},
            "config": {"voice_map": voice_map} if voice_map is not None else {},
        },
    ]
    if extra_generator:
        nodes.append({"id": "gen-2", "type": "operator_generator", "position": {"x": 2, "y": 0}, "config": {}})
    return {"graph": {"nodes": nodes, "edges": []}, "execution": {}}


def _voice_row(**overrides):
    row = {
        **_VOICE_JSON,
        "id": "v-ara",
        "name": "Ara",
        "provider": "naver",
        "provider_voice_id": "vara",
        "supported_languages": ["ko-kr"],
        "supported_models": ["clova"],
        "model_capabilities": [{"model": "clova", "languages_known": True, "supported_languages": ["ko-kr"]}],
    }
    row.update(overrides)
    return row


def _mock_set_voice(definition, voice=None):
    respx.get("https://api.onepin.ai/api/v1/workflows/wf-1").mock(
        return_value=httpx.Response(
            200, json={"data": {**_workflow_json("wf-1", "Alpha"), "definition": definition}, "meta": _META_JSON}
        )
    )
    respx.get("https://api.onepin.ai/api/v1/voices/v-ara").mock(
        return_value=httpx.Response(200, json={"data": voice or _voice_row(), "meta": _META_JSON})
    )
    return respx.patch("https://api.onepin.ai/api/v1/workflows/wf-1").mock(
        return_value=httpx.Response(
            200, json={"data": {**_workflow_json("wf-1", "Alpha"), "definition": definition}, "meta": _META_JSON}
        )
    )


_ARGV = [
    "--api-key",
    "op_live_x",
    "--no-color",
    "workflows",
    "set-voice",
    "wf-1",
    "--locale",
    "ko-kr",
    "--voice",
    "v-ara",
]


class TestWorkflowSetVoiceLocaleFamilies:
    """A declared bare family covers its regions, and vice versa.

    `supported_languages` legitimately carries a bare family — the API counts `ko` as
    official because `ko-kr` is, and `voices list --language ko-kr` returns voices that
    declared only `ko`. Exact matching rejected exactly the voices discovery recommends.
    """

    @respx.mock
    def test_declared_family_covers_a_regioned_locale(self, tmp_home) -> None:
        voice = _voice_row(
            supported_languages=["ko"],
            model_capabilities=[{"model": "clova", "languages_known": True, "supported_languages": ["ko"]}],
        )
        patch = _mock_set_voice(_generator_definition(), voice=voice)
        result = runner.invoke(app, _ARGV)
        assert result.exit_code == 0, result.output
        assert patch.called
        sent = json.loads(patch.calls[0].request.content)
        assigned = sent["definition"]["graph"]["nodes"][1]["config"]["voice_map"]["ko-kr"]
        assert assigned[0]["model"] == "clova"

    @respx.mock
    def test_declared_region_covers_a_bare_family_request(self, tmp_home) -> None:
        patch = _mock_set_voice(_generator_definition())
        result = runner.invoke(app, [*_ARGV[:6], "--locale", "ko", "--voice", "v-ara"])
        assert result.exit_code == 0, result.output
        assert patch.called

    @respx.mock
    def test_a_genuinely_unsupported_locale_is_still_rejected(self, tmp_home) -> None:
        patch = _mock_set_voice(_generator_definition())
        result = runner.invoke(app, [*_ARGV[:6], "--locale", "ja-jp", "--voice", "v-ara"])
        assert result.exit_code == 1
        assert "does not support ja-jp" in result.output
        assert not patch.called


class TestWorkflowSetVoicePreviousList:
    @respx.mock
    def test_every_replaced_assignment_is_named(self, tmp_home) -> None:
        """A locale slot holds a list; naming only the first loses the rest silently."""
        existing = {
            "ko-kr": [
                {
                    "voice_id": "vn",
                    "catalog_voice_id": "v-a",
                    "provider": "naver",
                    "model": "clova",
                    "voice_name": "Narrator",
                },
                {
                    "voice_id": "vs",
                    "catalog_voice_id": "v-b",
                    "provider": "naver",
                    "model": "clova",
                    "voice_name": "SecondSpeaker",
                },
            ]
        }
        _mock_set_voice(_generator_definition(voice_map=existing))
        result = runner.invoke(app, _ARGV)
        assert result.exit_code == 0, result.output
        assert "Narrator" in result.output
        assert "SecondSpeaker" in result.output


class TestWorkflowSetVoice:
    @respx.mock
    def test_writes_the_assignment_with_the_right_id_fields(self, tmp_home) -> None:
        """voice_id is the provider's id; catalog_voice_id is the UUID. Swapping them saves and
        then fails at run time, which is the mistake this command exists to remove."""
        patch = _mock_set_voice(_generator_definition())
        result = runner.invoke(app, _ARGV)
        assert result.exit_code == 0, result.output

        sent = json.loads(patch.calls[0].request.content)["definition"]
        generator = next(n for n in sent["graph"]["nodes"] if n["type"] == "operator_generator")
        assert generator["config"]["voice_map"]["ko-kr"] == [
            {
                "voice_id": "vara",
                "catalog_voice_id": "v-ara",
                "provider": "naver",
                "model": "clova",
                "voice_name": "Ara",
            }
        ]

    @respx.mock
    def test_other_nodes_are_left_alone(self, tmp_home) -> None:
        patch = _mock_set_voice(_generator_definition())
        assert runner.invoke(app, _ARGV).exit_code == 0

        sent = json.loads(patch.calls[0].request.content)["definition"]
        source = next(n for n in sent["graph"]["nodes"] if n["type"] == "source_script")
        assert source == {
            "id": "src-1",
            "type": "source_script",
            "position": {"x": 0, "y": 0},
            "config": {"text": "hi"},
        }

    @respx.mock
    def test_reports_what_it_replaced(self, tmp_home) -> None:
        existing = {
            "ko-kr": [
                {
                    "voice_id": "vdaeseong",
                    "catalog_voice_id": "v-ds",
                    "provider": "naver",
                    "model": "clova",
                    "voice_name": "Daeseong",
                }
            ]
        }
        _mock_set_voice(_generator_definition(voice_map=existing))
        result = runner.invoke(app, _ARGV)
        assert result.exit_code == 0, result.output
        assert "Set ko-kr to Ara (naver/clova)" in result.output
        assert "Previous: Daeseong (naver/clova), catalog id v-ds." in result.output
        assert "every future run uses the new voice" in result.output

    @respx.mock
    def test_other_locales_survive(self, tmp_home) -> None:
        existing = {"en-us": [{"voice_id": "ven", "provider": "eleven", "model": "v3", "voice_name": "Eve"}]}
        patch = _mock_set_voice(_generator_definition(voice_map=existing))
        assert runner.invoke(app, _ARGV).exit_code == 0

        sent = json.loads(patch.calls[0].request.content)["definition"]
        voice_map = next(n for n in sent["graph"]["nodes"] if n["type"] == "operator_generator")["config"]["voice_map"]
        assert voice_map["en-us"] == existing["en-us"]
        assert voice_map["ko-kr"][0]["voice_name"] == "Ara"

    @respx.mock
    def test_rejects_a_locale_the_voice_cannot_speak(self, tmp_home) -> None:
        patch = _mock_set_voice(_generator_definition(), voice=_voice_row(supported_languages=["en-us"]))
        result = runner.invoke(app, _ARGV)
        assert result.exit_code == 1
        assert "does not support ko-kr" in result.output
        assert not patch.called

    @respx.mock
    def test_rejects_a_model_that_does_not_cover_the_locale(self, tmp_home) -> None:
        voice = _voice_row(
            model_capabilities=[{"model": "clova", "languages_known": True, "supported_languages": ["en-us"]}]
        )
        patch = _mock_set_voice(_generator_definition(), voice=voice)
        result = runner.invoke(app, [*_ARGV, "--model", "clova"])
        assert result.exit_code == 1
        assert "does not cover ko-kr" in result.output
        assert not patch.called

    @respx.mock
    def test_rejects_an_inactive_voice(self, tmp_home) -> None:
        patch = _mock_set_voice(_generator_definition(), voice=_voice_row(is_active=False))
        result = runner.invoke(app, _ARGV)
        assert result.exit_code == 1
        assert "not active" in result.output
        assert not patch.called

    @respx.mock
    def test_refuses_to_guess_between_two_generators(self, tmp_home) -> None:
        patch = _mock_set_voice(_generator_definition(extra_generator=True))
        result = runner.invoke(app, _ARGV)
        assert result.exit_code == 1
        assert "AMBIGUOUS_NODE" in result.output
        assert "gen-1, gen-2" in result.output
        assert not patch.called

    @respx.mock
    def test_node_id_picks_one_of_several(self, tmp_home) -> None:
        patch = _mock_set_voice(_generator_definition(extra_generator=True))
        result = runner.invoke(app, [*_ARGV, "--node-id", "gen-2"])
        assert result.exit_code == 0, result.output

        sent = json.loads(patch.calls[0].request.content)["definition"]
        by_id = {n["id"]: n for n in sent["graph"]["nodes"]}
        assert "voice_map" in by_id["gen-2"]["config"]
        assert by_id["gen-1"]["config"] == {}

    @respx.mock
    def test_workflow_without_a_generator(self, tmp_home) -> None:
        definition = {
            "graph": {
                "nodes": [{"id": "src-1", "type": "source_script", "position": {"x": 0, "y": 0}, "config": {}}],
                "edges": [],
            },
            "execution": {},
        }
        patch = _mock_set_voice(definition)
        result = runner.invoke(app, _ARGV)
        assert result.exit_code == 1
        assert "no operator_generator node" in result.output
        assert not patch.called

    @respx.mock
    def test_json_carries_the_node_and_what_it_replaced(self, tmp_home) -> None:
        """The JSON shape is the undo record: node, locale, new assignment, and the old one."""
        previous = [
            {
                "voice_id": "ven",
                "catalog_voice_id": "v-eve",
                "provider": "eleven",
                "model": "v3",
                "voice_name": "Eve",
            }
        ]
        _mock_set_voice(_generator_definition(voice_map={"ko-kr": previous}))
        result = runner.invoke(app, [*_ARGV, "--json"])
        assert result.exit_code == 0, result.output

        payload = json.loads(result.output)
        assert payload["node_id"] == "gen-1"
        assert payload["locale"] == "ko-kr"
        assert payload["voice"]["catalog_voice_id"] == "v-ara"
        assert payload["previous"] == previous

    def test_a_voice_the_catalog_does_not_return_is_not_found(self) -> None:
        """Called directly: a null catalog row cannot be driven through a well-formed response,
        but it is what guards the ``voice_row[...]`` lookups below it."""
        with pytest.raises(CliError) as excinfo:
            composites._voice_assignment(None, "ko-kr", None)
        assert excinfo.value.code == "NOT_FOUND"

    @respx.mock
    def test_unknown_node_id_names_the_generators_present(self, tmp_home) -> None:
        patch = _mock_set_voice(_generator_definition(extra_generator=True))
        result = runner.invoke(app, [*_ARGV, "--node-id", "gen-9"])
        assert result.exit_code == 1
        assert "NOT_FOUND" in result.output
        assert "gen-1, gen-2" in result.output
        assert not patch.called

    @respx.mock
    def test_unknown_coverage_model_is_the_last_resort(self, tmp_home) -> None:
        """languages_known=False means the API cannot enumerate coverage, not that there is none."""
        voice = _voice_row(model_capabilities=[{"model": "clova", "languages_known": False, "supported_languages": []}])
        patch = _mock_set_voice(_generator_definition(), voice=voice)
        assert runner.invoke(app, _ARGV).exit_code == 0

        sent = json.loads(patch.calls[0].request.content)["definition"]
        generator = next(n for n in sent["graph"]["nodes"] if n["type"] == "operator_generator")
        assert generator["config"]["voice_map"]["ko-kr"][0]["model"] == "clova"

    @respx.mock
    def test_falls_back_to_supported_models_when_capabilities_are_empty(self, tmp_home) -> None:
        voice = _voice_row(model_capabilities=[], supported_models=["clova", "clova-lite"])
        patch = _mock_set_voice(_generator_definition(), voice=voice)
        assert runner.invoke(app, _ARGV).exit_code == 0

        sent = json.loads(patch.calls[0].request.content)["definition"]
        generator = next(n for n in sent["graph"]["nodes"] if n["type"] == "operator_generator")
        assert generator["config"]["voice_map"]["ko-kr"][0]["model"] == "clova"

    @respx.mock
    def test_voice_with_no_usable_model_is_rejected(self, tmp_home) -> None:
        voice = _voice_row(model_capabilities=[], supported_models=[])
        patch = _mock_set_voice(_generator_definition(), voice=voice)
        result = runner.invoke(app, _ARGV)
        assert result.exit_code == 1
        assert "lists no usable model for ko-kr" in result.output
        assert not patch.called

    @respx.mock
    def test_model_the_voice_does_not_have_lists_the_ones_it_does(self, tmp_home) -> None:
        patch = _mock_set_voice(_generator_definition())
        result = runner.invoke(app, [*_ARGV, "--model", "ghost"])
        assert result.exit_code == 1
        assert "has no model ghost" in result.output
        assert "It has: clova" in result.output
        assert not patch.called

    @respx.mock
    def test_model_is_matched_past_the_other_capabilities(self, tmp_home) -> None:
        voice = _voice_row(
            model_capabilities=[
                {"model": "clova-lite", "languages_known": True, "supported_languages": ["en-us"]},
                {"model": "clova", "languages_known": True, "supported_languages": ["ko-kr"]},
            ]
        )
        patch = _mock_set_voice(_generator_definition(), voice=voice)
        assert runner.invoke(app, [*_ARGV, "--model", "clova"]).exit_code == 0

        sent = json.loads(patch.calls[0].request.content)["definition"]
        generator = next(n for n in sent["graph"]["nodes"] if n["type"] == "operator_generator")
        assert generator["config"]["voice_map"]["ko-kr"][0]["model"] == "clova"

    @respx.mock
    def test_an_unreadable_previous_assignment_is_still_printed_verbatim(self, tmp_home) -> None:
        """Whatever was there has to be restorable, even when it is not the shape we write."""
        _mock_set_voice(_generator_definition(voice_map={"ko-kr": ["legacy-voice-id"]}))
        result = runner.invoke(app, _ARGV)
        assert result.exit_code == 0, result.output
        assert 'Previous: ["legacy-voice-id"]' in result.output


# === workflows duplicate =================================================================


def _workflow_json(workflow_id="wf-2", name="Alpha (Copy)"):
    return {
        "id": workflow_id,
        "user_id": "u",
        "name": name,
        "name_source": "user",
        "description": None,
        "definition": {"graph": {"nodes": [], "edges": []}, "execution": {}},
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    }


class TestWorkflowDuplicate:
    @respx.mock
    def test_without_name_does_not_patch(self, tmp_home) -> None:
        respx.post("https://api.onepin.ai/api/v1/workflows/wf-1/duplicate").mock(
            return_value=httpx.Response(201, json={"data": _workflow_json(), "meta": _META_JSON})
        )
        patch = respx.patch("https://api.onepin.ai/api/v1/workflows/wf-2")
        result = runner.invoke(app, ["--api-key", "op_live_x", "--no-color", "workflows", "duplicate", "wf-1"])
        assert result.exit_code == 0, result.output
        assert "Duplicated workflow into wf-2." in result.output
        assert not patch.called

    @respx.mock
    def test_name_is_applied_to_the_copy(self, tmp_home) -> None:
        respx.post("https://api.onepin.ai/api/v1/workflows/wf-1/duplicate").mock(
            return_value=httpx.Response(201, json={"data": _workflow_json(), "meta": _META_JSON})
        )
        patch = respx.patch("https://api.onepin.ai/api/v1/workflows/wf-2").mock(
            return_value=httpx.Response(200, json={"data": _workflow_json(name="Korean dub v2"), "meta": _META_JSON})
        )
        result = runner.invoke(
            app,
            ["--api-key", "op_live_x", "workflows", "duplicate", "wf-1", "--name", "Korean dub v2", "--json"],
        )
        assert result.exit_code == 0, result.output
        assert json.loads(patch.calls[0].request.content) == {"name": "Korean dub v2"}
        assert json.loads(result.output)["name"] == "Korean dub v2"

    @respx.mock
    def test_failed_rename_still_names_the_new_id(self, tmp_home) -> None:
        """The copy exists even when the second call fails; losing its id strands it."""
        respx.post("https://api.onepin.ai/api/v1/workflows/wf-1/duplicate").mock(
            return_value=httpx.Response(201, json={"data": _workflow_json(), "meta": _META_JSON})
        )
        respx.patch("https://api.onepin.ai/api/v1/workflows/wf-2").mock(
            return_value=httpx.Response(422, json={"error": {"code": "VALIDATION_ERROR", "message": "bad name"}})
        )
        result = runner.invoke(
            app, ["--api-key", "op_live_x", "workflows", "duplicate", "wf-1", "--name", "Korean dub v2"]
        )
        assert result.exit_code == 1
        assert "RENAME_FAILED" in result.output
        assert "wf-2" in result.output

    @respx.mock
    def test_blank_name_is_rejected_before_duplicating(self, tmp_home) -> None:
        duplicate = respx.post("https://api.onepin.ai/api/v1/workflows/wf-1/duplicate")
        result = runner.invoke(app, ["--api-key", "op_live_x", "workflows", "duplicate", "wf-1", "--name", "  "])
        assert result.exit_code == 1
        assert "INVALID_ARGUMENTS" in result.output
        assert not duplicate.called


# === voices sample =======================================================================


_VOICE_JSON = {
    "id": "v-1",
    "name": "Ara",
    "provider": "naver",
    "provider_voice_id": "vara",
    "is_active": True,
    "sample_url": "https://cdn.example/ara-default.mp3?Signature=abc",
    "language_sample_url": None,
    "language_sample_locale": "en-us",
    "supported_languages": ["ko-kr"],
    "supported_models": ["clova"],
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
}


def _preview_json(name="Ara", locale="ko-kr", url="https://cdn.example/ara-ko.mp3?Signature=abc"):
    return {"name": name, "locale": locale, "model": "clova", "sample_url": url, "content_type": "audio/mpeg"}


class TestVoicesSampleDestinations:
    @respx.mock
    def test_same_named_voices_do_not_overwrite_each_other(self, tmp_home, tmp_path) -> None:
        """Display names are not unique across providers; two "Sarah"s must not collide.

        Colliding stems previously wrote both rows to one path, reported two files, and
        exited 0 — one sample silently lost.
        """
        for voice_id, url in (("v-1", "https://cdn.example/a.mp3"), ("v-2", "https://cdn.example/b.mp3")):
            respx.get(f"https://api.onepin.ai/api/v1/voices/{voice_id}/preview").mock(
                return_value=httpx.Response(
                    200, json={"data": _preview_json("Sarah", url=f"{url}?Signature=x"), "meta": _META_JSON}
                )
            )
        respx.get("https://cdn.example/a.mp3").mock(return_value=httpx.Response(200, content=b"AAAA"))
        respx.get("https://cdn.example/b.mp3").mock(return_value=httpx.Response(200, content=b"BBBB"))

        out_dir = tmp_path / "s"
        out_dir.mkdir()
        result = runner.invoke(
            app,
            [
                "--api-key",
                "op_live_x",
                "--no-color",
                "voices",
                "sample",
                "v-1",
                "v-2",
                "--language",
                "ko-kr",
                "--out-dir",
                str(out_dir),
            ],
        )
        assert result.exit_code == 0, result.output
        written = sorted(path.read_bytes() for path in out_dir.iterdir())
        assert written == [b"AAAA", b"BBBB"], sorted(p.name for p in out_dir.iterdir())

    @respx.mock
    def test_distinct_names_keep_readable_filenames(self, tmp_home, tmp_path) -> None:
        """Only colliding stems get disambiguated — the common case stays legible."""
        respx.get("https://api.onepin.ai/api/v1/voices/v-1/preview").mock(
            return_value=httpx.Response(200, json={"data": _preview_json(), "meta": _META_JSON})
        )
        respx.get("https://cdn.example/ara-ko.mp3").mock(return_value=httpx.Response(200, content=b"ID3ara"))

        out_dir = tmp_path / "s"
        out_dir.mkdir()
        result = runner.invoke(
            app,
            [
                "--api-key",
                "op_live_x",
                "--no-color",
                "voices",
                "sample",
                "v-1",
                "--language",
                "ko-kr",
                "--out-dir",
                str(out_dir),
            ],
        )
        assert result.exit_code == 0, result.output
        assert [path.name for path in out_dir.iterdir()] == ["Ara-ko-kr.mp3"]


class TestVoicesSample:
    @respx.mock
    def test_prints_url_when_no_destination(self, tmp_home) -> None:
        respx.get("https://api.onepin.ai/api/v1/voices/v-1/preview").mock(
            return_value=httpx.Response(200, json={"data": _preview_json(), "meta": _META_JSON})
        )
        result = runner.invoke(
            app, ["--api-key", "op_live_x", "--no-color", "voices", "sample", "v-1", "--language", "ko-kr"]
        )
        assert result.exit_code == 0, result.output
        assert "Ara (ko-kr)" in result.output
        assert "https://cdn.example/ara-ko.mp3" in result.output

    @respx.mock
    def test_writes_one_file_per_voice(self, tmp_home, tmp_path) -> None:
        respx.get("https://api.onepin.ai/api/v1/voices/v-1/preview").mock(
            return_value=httpx.Response(200, json={"data": _preview_json(), "meta": _META_JSON})
        )
        respx.get("https://api.onepin.ai/api/v1/voices/v-2/preview").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": _preview_json("Daeseong", url="https://cdn.example/ds-ko.mp3?Signature=x"),
                    "meta": _META_JSON,
                },
            )
        )
        respx.get("https://cdn.example/ara-ko.mp3").mock(return_value=httpx.Response(200, content=b"ID3ara"))
        respx.get("https://cdn.example/ds-ko.mp3").mock(return_value=httpx.Response(200, content=b"ID3ds"))

        result = runner.invoke(
            app,
            [
                "--api-key",
                "op_live_x",
                "--no-color",
                "voices",
                "sample",
                "v-1",
                "v-2",
                "--language",
                "ko-kr",
                "--out-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0, result.output
        assert (tmp_path / "Ara-ko-kr.mp3").read_bytes() == b"ID3ara"
        assert (tmp_path / "Daeseong-ko-kr.mp3").read_bytes() == b"ID3ds"

    @respx.mock
    def test_falls_back_to_default_sample_and_says_so(self, tmp_home) -> None:
        """A 404 means no preview *in that locale*, not a voice that cannot speak it."""
        respx.get("https://api.onepin.ai/api/v1/voices/v-1/preview").mock(
            return_value=httpx.Response(404, json={"error": {"code": "NOT_FOUND", "message": "no preview"}})
        )
        respx.get("https://api.onepin.ai/api/v1/voices/v-1").mock(
            return_value=httpx.Response(200, json={"data": _VOICE_JSON, "meta": _META_JSON})
        )
        result = runner.invoke(
            app, ["--api-key", "op_live_x", "--no-color", "voices", "sample", "v-1", "--language", "ko-kr"]
        )
        assert result.exit_code == 0, result.output
        assert "no preview in the requested locale" in result.output
        assert "ara-default.mp3" in result.output

    @respx.mock
    def test_no_language_uses_the_default_sample(self, tmp_home) -> None:
        preview = respx.get("https://api.onepin.ai/api/v1/voices/v-1/preview")
        respx.get("https://api.onepin.ai/api/v1/voices/v-1").mock(
            return_value=httpx.Response(200, json={"data": _VOICE_JSON, "meta": _META_JSON})
        )
        result = runner.invoke(app, ["--api-key", "op_live_x", "--no-color", "voices", "sample", "v-1"])
        assert result.exit_code == 0, result.output
        assert not preview.called
        assert "ara-default.mp3" in result.output

    @respx.mock
    def test_refuses_to_clobber_without_force(self, tmp_home, tmp_path) -> None:
        respx.get("https://api.onepin.ai/api/v1/voices/v-1/preview").mock(
            return_value=httpx.Response(200, json={"data": _preview_json(), "meta": _META_JSON})
        )
        respx.get("https://cdn.example/ara-ko.mp3").mock(return_value=httpx.Response(200, content=b"new"))
        dest = tmp_path / "keep.mp3"
        dest.write_bytes(b"original")

        argv = ["--api-key", "op_live_x", "voices", "sample", "v-1", "--language", "ko-kr", "--out", str(dest)]
        blocked = runner.invoke(app, argv)
        assert blocked.exit_code == 1
        assert "FILE_EXISTS" in blocked.output
        assert dest.read_bytes() == b"original"

        forced = runner.invoke(app, [*argv, "--force"])
        assert forced.exit_code == 0, forced.output
        assert dest.read_bytes() == b"new"

    @respx.mock
    def test_out_rejects_multiple_voices(self, tmp_home, tmp_path) -> None:
        result = runner.invoke(
            app,
            ["--api-key", "op_live_x", "voices", "sample", "v-1", "v-2", "--out", str(tmp_path / "x.mp3")],
        )
        assert result.exit_code == 1
        assert "INVALID_ARGUMENTS" in result.output

    @respx.mock
    def test_no_sample_anywhere_is_an_error(self, tmp_home) -> None:
        respx.get("https://api.onepin.ai/api/v1/voices/v-1").mock(
            return_value=httpx.Response(200, json={"data": {**_VOICE_JSON, "sample_url": None}, "meta": _META_JSON})
        )
        result = runner.invoke(app, ["--api-key", "op_live_x", "voices", "sample", "v-1"])
        assert result.exit_code == 1
        assert "NO_SAMPLE" in result.output

    @respx.mock
    def test_json_rows_carry_the_fallback_flag(self, tmp_home) -> None:
        respx.get("https://api.onepin.ai/api/v1/voices/v-1/preview").mock(
            return_value=httpx.Response(200, json={"data": _preview_json(), "meta": _META_JSON})
        )
        result = runner.invoke(
            app, ["--api-key", "op_live_x", "voices", "sample", "v-1", "--language", "ko-kr", "--json"]
        )
        assert result.exit_code == 0, result.output
        rows = json.loads(result.output)
        assert rows[0]["locale"] == "ko-kr"
        assert rows[0]["fallback"] is False

    @respx.mock
    def test_play_hands_a_real_file_to_the_player(self, tmp_home, monkeypatch) -> None:
        """afplay takes a path, not a URL — the bytes must be on disk before it is called."""
        import shutil
        import subprocess

        respx.get("https://api.onepin.ai/api/v1/voices/v-1/preview").mock(
            return_value=httpx.Response(200, json={"data": _preview_json(), "meta": _META_JSON})
        )
        respx.get("https://cdn.example/ara-ko.mp3").mock(return_value=httpx.Response(200, content=b"ID3ara"))

        calls: list[list[str]] = []

        def _fake_run(command, **kwargs):
            calls.append(command)
            assert Path(command[-1]).read_bytes() == b"ID3ara"
            return subprocess.CompletedProcess(command, 0)

        monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")
        monkeypatch.setattr(subprocess, "run", _fake_run)

        result = runner.invoke(
            app,
            ["--api-key", "op_live_x", "--no-color", "voices", "sample", "v-1", "--language", "ko-kr", "--play"],
        )
        assert result.exit_code == 0, result.output
        assert len(calls) == 1
        assert "Playing 1/1 Ara (ko-kr)" in result.output

    @respx.mock
    def test_play_names_each_voice_before_its_clip(self, tmp_home, monkeypatch) -> None:
        """A shortlist played in one call is only followable if the label lands before the audio."""
        import shutil
        import subprocess

        respx.get("https://api.onepin.ai/api/v1/voices/v-1/preview").mock(
            return_value=httpx.Response(200, json={"data": _preview_json(), "meta": _META_JSON})
        )
        respx.get("https://api.onepin.ai/api/v1/voices/v-2/preview").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": _preview_json("Daeseong", url="https://cdn.example/ds-ko.mp3?Signature=x"),
                    "meta": _META_JSON,
                },
            )
        )
        respx.get("https://cdn.example/ara-ko.mp3").mock(return_value=httpx.Response(200, content=b"ID3ara"))
        respx.get("https://cdn.example/ds-ko.mp3").mock(return_value=httpx.Response(200, content=b"ID3ds"))

        def _fake_run(command, **kwargs):
            # Stands in for the noise the player makes, so ordering is visible in the output.
            print(f"<audio {Path(command[-1]).name}>")
            return subprocess.CompletedProcess(command, 0)

        monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")
        monkeypatch.setattr(subprocess, "run", _fake_run)

        result = runner.invoke(
            app,
            ["--api-key", "op_live_x", "--no-color", "voices", "sample", "v-1", "v-2", "--language", "ko-kr", "--play"],
        )
        assert result.exit_code == 0, result.output
        lines = [line for line in result.output.splitlines() if line.strip()]
        assert lines[0].startswith("Playing 1/2 Ara (ko-kr)")
        assert lines[1] == "<audio Ara-ko-kr.mp3>"
        assert lines[2].startswith("Playing 2/2 Daeseong (ko-kr)")
        assert lines[3] == "<audio Daeseong-ko-kr.mp3>"

    @respx.mock
    def test_missing_player_warns_but_keeps_the_file(self, tmp_home, tmp_path, monkeypatch) -> None:
        """No audio device is not a failed command — the bytes were still fetched and written."""
        import shutil

        respx.get("https://api.onepin.ai/api/v1/voices/v-1/preview").mock(
            return_value=httpx.Response(200, json={"data": _preview_json(), "meta": _META_JSON})
        )
        respx.get("https://cdn.example/ara-ko.mp3").mock(return_value=httpx.Response(200, content=b"ID3ara"))
        monkeypatch.setattr(shutil, "which", lambda name: None)

        dest = tmp_path / "ara.mp3"
        result = runner.invoke(
            app,
            [
                "--api-key",
                "op_live_x",
                "--no-color",
                "voices",
                "sample",
                "v-1",
                "--language",
                "ko-kr",
                "--play",
                "--out",
                str(dest),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "No audio player found" in result.output
        assert dest.read_bytes() == b"ID3ara"

    def test_name_is_not_trusted_into_a_path(self, tmp_path) -> None:
        """A server-supplied name carrying separators must not escape --out-dir."""
        stem = composites._sample_stem({"name": "../../etc/passwd", "locale": "ko-kr", "voice_id": "v-1"})
        assert "/" not in stem and ".." not in stem

    @respx.mock
    def test_out_and_out_dir_together_are_rejected(self, tmp_home, tmp_path) -> None:
        result = runner.invoke(
            app,
            [
                "--api-key",
                "op_live_x",
                "voices",
                "sample",
                "v-1",
                "--out",
                str(tmp_path / "x.mp3"),
                "--out-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 1
        assert "INVALID_ARGUMENTS" in result.output

    @respx.mock
    def test_out_dir_must_already_exist(self, tmp_home, tmp_path) -> None:
        """Failing before the fetch keeps a paid-for sample from being downloaded into nowhere."""
        result = runner.invoke(
            app,
            ["--api-key", "op_live_x", "voices", "sample", "v-1", "--out-dir", str(tmp_path / "nope")],
        )
        assert result.exit_code == 1
        assert "DIRECTORY_NOT_FOUND" in result.output

    @respx.mock
    def test_anything_but_a_404_from_preview_propagates(self, tmp_home) -> None:
        """Only a missing per-locale preview degrades; a broken endpoint must not look like one."""
        respx.get("https://api.onepin.ai/api/v1/voices/v-1/preview").mock(
            return_value=httpx.Response(500, json={"error": {"code": "INTERNAL_ERROR", "message": "boom"}})
        )
        fallback = respx.get("https://api.onepin.ai/api/v1/voices/v-1")
        result = runner.invoke(
            app, ["--api-key", "op_live_x", "--no-color", "voices", "sample", "v-1", "--language", "ko-kr"]
        )
        assert result.exit_code == 1
        assert "INTERNAL_ERROR" in result.output
        assert not fallback.called

    @respx.mock
    def test_play_with_json_still_emits_the_rows(self, tmp_home, monkeypatch) -> None:
        """--play prints nothing readable, so --json has to carry the paths for the caller."""
        import shutil
        import subprocess

        respx.get("https://api.onepin.ai/api/v1/voices/v-1/preview").mock(
            return_value=httpx.Response(200, json={"data": _preview_json(), "meta": _META_JSON})
        )
        respx.get("https://cdn.example/ara-ko.mp3").mock(return_value=httpx.Response(200, content=b"ID3ara"))
        monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")
        monkeypatch.setattr(subprocess, "run", lambda command, **kw: subprocess.CompletedProcess(command, 0))

        result = runner.invoke(
            app,
            [
                "--api-key",
                "op_live_x",
                "voices",
                "sample",
                "v-1",
                "--language",
                "ko-kr",
                "--play",
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        rows = json.loads(result.output)
        assert Path(rows[0]["path"]).read_bytes() == b"ID3ara"

    @respx.mock
    def test_an_unreachable_cdn_is_a_download_error(self, tmp_home, tmp_path) -> None:
        respx.get("https://api.onepin.ai/api/v1/voices/v-1/preview").mock(
            return_value=httpx.Response(200, json={"data": _preview_json(), "meta": _META_JSON})
        )
        respx.get("https://cdn.example/ara-ko.mp3").mock(side_effect=httpx.ConnectError("no route"))

        dest = tmp_path / "ara.mp3"
        result = runner.invoke(
            app,
            [
                "--api-key",
                "op_live_x",
                "--no-color",
                "voices",
                "sample",
                "v-1",
                "--language",
                "ko-kr",
                "--out",
                str(dest),
            ],
        )
        assert result.exit_code == 1
        assert "DOWNLOAD_FAILED" in result.output
        assert not dest.exists()

    @respx.mock
    def test_an_expired_presigned_url_says_so(self, tmp_home, tmp_path) -> None:
        respx.get("https://api.onepin.ai/api/v1/voices/v-1/preview").mock(
            return_value=httpx.Response(200, json={"data": _preview_json(), "meta": _META_JSON})
        )
        respx.get("https://cdn.example/ara-ko.mp3").mock(return_value=httpx.Response(403, content=b"expired"))

        dest = tmp_path / "ara.mp3"
        result = runner.invoke(
            app,
            [
                "--api-key",
                "op_live_x",
                "--no-color",
                "voices",
                "sample",
                "v-1",
                "--language",
                "ko-kr",
                "--out",
                str(dest),
            ],
        )
        assert result.exit_code == 1
        assert "may have expired" in result.output
        assert not dest.exists()

    @respx.mock
    def test_a_player_that_fails_warns_but_keeps_the_file(self, tmp_home, tmp_path, monkeypatch) -> None:
        """The bytes are already paid for and on disk; a player crash must not throw them away."""
        import shutil
        import subprocess

        respx.get("https://api.onepin.ai/api/v1/voices/v-1/preview").mock(
            return_value=httpx.Response(200, json={"data": _preview_json(), "meta": _META_JSON})
        )
        respx.get("https://cdn.example/ara-ko.mp3").mock(return_value=httpx.Response(200, content=b"ID3ara"))

        def _explode(command, **kwargs):
            raise subprocess.CalledProcessError(1, command)

        monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")
        monkeypatch.setattr(subprocess, "run", _explode)

        dest = tmp_path / "ara.mp3"
        result = runner.invoke(
            app,
            [
                "--api-key",
                "op_live_x",
                "--no-color",
                "voices",
                "sample",
                "v-1",
                "--language",
                "ko-kr",
                "--play",
                "--out",
                str(dest),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "Could not play" in result.output
        assert dest.read_bytes() == b"ID3ara"

    @pytest.mark.parametrize(
        ("platform", "player"),
        [("darwin", "afplay"), ("win32", "powershell"), ("linux", "ffplay")],
    )
    def test_each_platform_reaches_for_its_own_player(self, tmp_path, monkeypatch, platform, player) -> None:
        import shutil
        import subprocess
        import sys

        commands: list[list[str]] = []

        def _record(command, **kwargs):
            commands.append(command)
            return subprocess.CompletedProcess(command, 0)

        monkeypatch.setattr(sys, "platform", platform)
        monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")
        monkeypatch.setattr(subprocess, "run", _record)

        composites._play_audio(tmp_path / "ara.mp3", False)
        assert commands[0][0] == player
        assert commands[0][-1] == str(tmp_path / "ara.mp3")


# === local schema commands ===============================================================


class TestSchemas:
    def test_definition_schema_is_valid_json(self, tmp_home) -> None:
        result = runner.invoke(app, ["workflows", "definition-schema"])
        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        assert "properties" in parsed

    def test_top_level_schema_is_valid_json(self, tmp_home) -> None:
        result = runner.invoke(app, ["schema"])
        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        assert parsed["name"] == "onepin"
        assert any(c["path"] == ["workflows", "list"] for c in parsed["commands"])
