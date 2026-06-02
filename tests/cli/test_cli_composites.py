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


# === workflows run [--watch] =============================================================


class _Runs:
    def __init__(self, statuses: list[str]) -> None:
        self._statuses = statuses
        self._i = 0

    def start(self, workflow_id, **kw):
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
