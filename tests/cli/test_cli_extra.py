"""Additional coverage: comma_list, workspace forwarding, list mode, keyvalue, watch Ctrl-C, dl errors."""

from __future__ import annotations

import datetime as dt

import httpx
import respx
from typer.testing import CliRunner

from onepin._cli import _dispatch
from onepin._cli.commands import composites
from onepin._cli.main import app

runner = CliRunner()
NOW = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)


def _meta():
    from onepin.types.meta import Meta

    return Meta(request_id="r1", timestamp=NOW)


class TestCommaListAndCapture:
    """voices list --language a,b must split into a list and forward to the SDK."""

    def test_language_comma_split_forwarded(self, monkeypatch, tmp_home) -> None:
        captured = {}
        from onepin.core.pagination import SyncPager

        class Voices:
            def list(self, **kw):
                captured.update(kw)
                return SyncPager(get_next=None, has_next=False, items=[], response=None)

        client = type("C", (), {"voices": Voices()})()
        monkeypatch.setattr(_dispatch, "get_client", lambda: client)
        result = runner.invoke(app, ["--api-key", "op_live_x", "voices", "list", "--language", "en-us,ko-kr"])
        assert result.exit_code == 0, result.output
        assert captured.get("language") == ["en-us", "ko-kr"]


class TestWorkspaceForwarding:
    def test_workspace_forwarded_when_method_accepts(self, monkeypatch, tmp_home) -> None:
        captured = {}
        from onepin.core.pagination import SyncPager

        class Workflows:
            def list(self, *, workspace_id=None, **kw):
                captured["workspace_id"] = workspace_id
                return SyncPager(get_next=None, has_next=False, items=[], response=None)

        client = type("C", (), {"workflows": Workflows()})()
        monkeypatch.setattr(_dispatch, "get_client", lambda: client)
        result = runner.invoke(app, ["--api-key", "op_live_x", "--workspace", "ws-42", "workflows", "list"])
        assert result.exit_code == 0, result.output
        assert captured["workspace_id"] == "ws-42"

    def test_workspace_not_forwarded_when_path_param_named_workspace_id(self, monkeypatch, tmp_home) -> None:
        # workspaces.get_workspace takes workspace_id POSITIONALLY (path param), so the root
        # --workspace must NOT be injected as a kwarg. Mirror the real SDK signature.
        captured = {}

        class Workspaces:
            def get_workspace(self, workspace_id, *, request_options=None):
                captured["positional"] = workspace_id
                from onepin.types import ApiResponseWorkspaceOut, WorkspaceOut

                ws = WorkspaceOut(
                    id=workspace_id,
                    name="n",
                    slug="s",
                    color_idx=0,
                    routing_price_sensitivity=0.5,
                    routing_llm_fit=True,
                    created_by="u",
                    created_at=NOW,
                    updated_at=NOW,
                )
                return ApiResponseWorkspaceOut(data=ws, meta=_meta())

        client = type("C", (), {"workspaces": Workspaces()})()
        monkeypatch.setattr(_dispatch, "get_client", lambda: client)
        result = runner.invoke(
            app, ["--api-key", "op_live_x", "--workspace", "ws-root", "workspace", "show", "ws-1", "--json"]
        )
        assert result.exit_code == 0, result.output
        assert captured["positional"] == "ws-1"
        # get_workspace declares **kw here, but real SDK has no workspace_id kwarg -> none injected.


class TestKeyValueRender:
    def test_data_mode_keyvalue_output(self, monkeypatch, tmp_home) -> None:
        from onepin.types import ApiResponseWorkspaceOut, WorkspaceOut

        class Workspaces:
            def get_workspace(self, workspace_id, **kw):
                ws = WorkspaceOut(
                    id=workspace_id,
                    name="Main",
                    slug="main",
                    color_idx=2,
                    routing_price_sensitivity=0.5,
                    routing_llm_fit=True,
                    created_by="u",
                    created_at=NOW,
                    updated_at=NOW,
                )
                return ApiResponseWorkspaceOut(data=ws, meta=_meta())

        client = type("C", (), {"workspaces": Workspaces()})()
        monkeypatch.setattr(_dispatch, "get_client", lambda: client)
        result = runner.invoke(app, ["--api-key", "op_live_x", "--no-color", "workspace", "show", "ws-1"])
        assert result.exit_code == 0, result.output
        assert "name: Main" in result.output
        assert "color_idx: 2" in result.output


class TestListMode:
    def test_list_mode_table(self, monkeypatch, tmp_home) -> None:
        from onepin.types import ApiListResponseWorkspaceMemberOut, WorkspaceMemberOut

        class Members:
            def list_members(self, ws_id, **kw):
                m = WorkspaceMemberOut(
                    id="m-1",
                    user_id="u-1",
                    email="a@b.com",
                    first_name="A",
                    last_name="B",
                    image_url=None,
                    role="admin",
                    last_active_at=NOW,
                    status="active",
                )
                from onepin.types import PaginationMeta

                return ApiListResponseWorkspaceMemberOut(
                    data=[m], meta=_meta(), pagination=PaginationMeta(next=None, prev=None, limit=50)
                )

        client = type("C", (), {"workspace_members": Members()})()
        monkeypatch.setattr(_dispatch, "get_client", lambda: client)
        result = runner.invoke(app, ["--api-key", "op_live_x", "--no-color", "workspace", "members", "list", "ws-1"])
        assert result.exit_code == 0, result.output
        assert "a@b.com" in result.output


class TestWatchInterrupt:
    def test_ctrl_c_during_watch_exits_130(self, monkeypatch, tmp_home) -> None:
        from onepin.types import ApiResponseWorkflowRunOut, WorkflowRunOut

        def _run(status):
            run = WorkflowRunOut(
                id="run-1",
                workflow_id="wf-1",
                status=status,
                run_number=1,
                total_nodes=1,
                total_steps=1,
                finished_steps=0,
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

        class Runs:
            def start(self, workflow_id, **kw):
                return _run("running")

            def status(self, workflow_id, run_id, **kw):
                raise KeyboardInterrupt()

        client = type("C", (), {"workflows": type("W", (), {"runs": Runs()})()})()
        monkeypatch.setattr(composites, "get_client", lambda: client)
        monkeypatch.setattr(composites.time, "sleep", lambda s: None)
        result = runner.invoke(app, ["--api-key", "op_live_x", "workflows", "run", "wf-1", "--watch"])
        assert result.exit_code == 130
        assert "Interrupted" in result.output


class TestDownloadErrors:
    @respx.mock
    def test_download_network_error(self, monkeypatch, tmp_home, tmp_path) -> None:
        from onepin.types import ApiResponseDownloadUrlOut, DownloadUrlOut

        class Wf:
            def download_run(self, workflow_id, run_id, **kw):
                return ApiResponseDownloadUrlOut(
                    data=DownloadUrlOut(url="https://s3.example.com/get", filename="o", expires_at=NOW),
                    meta=_meta(),
                )

        client = type("C", (), {"workflows": Wf()})()
        monkeypatch.setattr(composites, "get_client", lambda: client)
        respx.get("https://s3.example.com/get").mock(side_effect=httpx.ConnectError("down"))
        out = tmp_path / "o.zip"
        result = runner.invoke(
            app, ["--api-key", "op_live_x", "workflows", "runs", "download", "wf-1", "run-1", "--out", str(out)]
        )
        assert result.exit_code == 1
        assert "DOWNLOAD_FAILED" in result.output

    @respx.mock
    def test_download_node_to_missing_dir(self, monkeypatch, tmp_home, tmp_path) -> None:
        from onepin.types import ApiResponseDownloadUrlOut, DownloadUrlOut

        class Wf:
            def download_run_node(self, workflow_id, run_id, node_id, **kw):
                return ApiResponseDownloadUrlOut(
                    data=DownloadUrlOut(url="https://s3.example.com/n", filename="o", expires_at=NOW),
                    meta=_meta(),
                )

        client = type("C", (), {"workflows": Wf()})()
        monkeypatch.setattr(composites, "get_client", lambda: client)
        respx.get("https://s3.example.com/n").mock(return_value=httpx.Response(200, content=b"X"))
        out = tmp_path / "missing-dir" / "o.zip"
        result = runner.invoke(
            app,
            [
                "--api-key",
                "op_live_x",
                "workflows",
                "runs",
                "download-node",
                "wf-1",
                "run-1",
                "node-1",
                "--out",
                str(out),
            ],
        )
        assert result.exit_code == 1
        assert "DOWNLOAD_FAILED" in result.output


class TestDownloadToctouRace:
    """A file created AFTER the early existence check must NOT be clobbered without --force."""

    @respx.mock
    def test_file_created_mid_download_not_clobbered(self, monkeypatch, tmp_home, tmp_path) -> None:
        from onepin.types import ApiResponseDownloadUrlOut, DownloadUrlOut

        out = tmp_path / "race.zip"

        class Wf:
            def download_run(self, workflow_id, run_id, **kw):
                # Simulate a file appearing after the early check but before _atomic_write.
                out.write_bytes(b"PRECIOUS")
                return ApiResponseDownloadUrlOut(
                    data=DownloadUrlOut(url="https://s3.example.com/get", filename="o", expires_at=NOW),
                    meta=_meta(),
                )

        client = type("C", (), {"workflows": Wf()})()
        monkeypatch.setattr(composites, "get_client", lambda: client)
        respx.get("https://s3.example.com/get").mock(return_value=httpx.Response(200, content=b"OVERWRITE"))

        result = runner.invoke(
            app, ["--api-key", "op_live_x", "workflows", "runs", "download", "wf-1", "run-1", "--out", str(out)]
        )
        assert result.exit_code == 1
        assert "FILE_EXISTS" in result.output
        # The original file must NOT have been clobbered.
        assert out.read_bytes() == b"PRECIOUS"

    @respx.mock
    def test_force_overwrites_despite_race(self, monkeypatch, tmp_home, tmp_path) -> None:
        from onepin.types import ApiResponseDownloadUrlOut, DownloadUrlOut

        out = tmp_path / "race.zip"
        out.write_bytes(b"OLD")

        class Wf:
            def download_run(self, workflow_id, run_id, **kw):
                return ApiResponseDownloadUrlOut(
                    data=DownloadUrlOut(url="https://s3.example.com/get", filename="o", expires_at=NOW),
                    meta=_meta(),
                )

        client = type("C", (), {"workflows": Wf()})()
        monkeypatch.setattr(composites, "get_client", lambda: client)
        respx.get("https://s3.example.com/get").mock(return_value=httpx.Response(200, content=b"NEW"))

        result = runner.invoke(
            app,
            ["--api-key", "op_live_x", "workflows", "runs", "download", "wf-1", "run-1", "--out", str(out), "--force"],
        )
        assert result.exit_code == 0, result.output
        assert out.read_bytes() == b"NEW"


class TestBoolFilterDefaultOmitted:
    """Boolean filter flags at their default must NOT be forwarded to the SDK."""

    def test_favorites_only_omitted_when_not_passed(self, monkeypatch, tmp_home) -> None:
        captured = {}
        from onepin.core.pagination import SyncPager

        class Templates:
            def list(self, **kw):
                captured.update(kw)
                return SyncPager(get_next=None, has_next=False, items=[], response=None)

        client = type("C", (), {"templates": Templates()})()
        monkeypatch.setattr(_dispatch, "get_client", lambda: client)
        result = runner.invoke(app, ["--api-key", "op_live_x", "templates", "list"])
        assert result.exit_code == 0, result.output
        # favorites_only=False should NOT be in the call -- SDK default is None.
        assert "favorites_only" not in captured

    def test_favorites_only_forwarded_when_passed(self, monkeypatch, tmp_home) -> None:
        captured = {}
        from onepin.core.pagination import SyncPager

        class Templates:
            def list(self, **kw):
                captured.update(kw)
                return SyncPager(get_next=None, has_next=False, items=[], response=None)

        client = type("C", (), {"templates": Templates()})()
        monkeypatch.setattr(_dispatch, "get_client", lambda: client)
        result = runner.invoke(app, ["--api-key", "op_live_x", "templates", "list", "--favorites-only"])
        assert result.exit_code == 0, result.output
        assert captured.get("favorites_only") is True


class TestWatchInterruptJson:
    """Ctrl-C under --json --watch must emit structured error envelope to stderr."""

    def test_ctrl_c_json_emits_error_envelope(self, monkeypatch, tmp_home) -> None:
        from onepin.types import ApiResponseWorkflowRunOut, WorkflowRunOut

        def _run(status):
            run = WorkflowRunOut(
                id="run-1",
                workflow_id="wf-1",
                status=status,
                run_number=1,
                total_nodes=1,
                total_steps=1,
                finished_steps=0,
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

        class Runs:
            def start(self, workflow_id, **kw):
                return _run("running")

            def status(self, workflow_id, run_id, **kw):
                raise KeyboardInterrupt()

        client = type("C", (), {"workflows": type("W", (), {"runs": Runs()})()})()
        monkeypatch.setattr(composites, "get_client", lambda: client)
        monkeypatch.setattr(composites.time, "sleep", lambda s: None)
        result = runner.invoke(app, ["--api-key", "op_live_x", "workflows", "run", "wf-1", "--watch", "--json"])
        assert result.exit_code == 130
        assert "INTERRUPTED" in result.output
        assert "last_status" in result.output


class TestRichTableRender:
    def test_rich_table_path(self, monkeypatch, capsys) -> None:
        from onepin._cli import render

        monkeypatch.setattr(render, "_use_color", lambda: True)
        render.render_table([{"id": "1", "name": "Alpha"}], columns=["id", "name"], title="Workflows")
        out = capsys.readouterr().out
        assert "Alpha" in out
