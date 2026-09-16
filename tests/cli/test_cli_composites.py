"""Tests for hand-written composite commands: run/watch, uploads create, downloads, schemas."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import httpx
import pytest
import respx
from typer.testing import CliRunner

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
        assert "Played Ara (ko-kr)" in result.output

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
