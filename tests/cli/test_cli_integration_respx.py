"""respx integration tests: exercise the real SDK serialization for one command per unwrap mode.

Unlike the fake-client CLI tests, these build a real ``OnePinClient`` and mock only the HTTP
transport, so the actual Fern request-building + response-parsing path is covered end to end.
"""

from __future__ import annotations

import httpx
import respx
from typer.testing import CliRunner

from onepin._cli.main import app

runner = CliRunner()
_BASE = "https://api.onepin.ai"

_META = {"request_id": "01JTEST00000000000000000000", "timestamp": "2025-01-01T00:00:00Z"}


def _invoke(argv: list[str]):
    return runner.invoke(app, ["--api-key", "op_live_x", *argv])


class TestPagerMode:
    @respx.mock
    def test_workflows_list(self, tmp_home) -> None:
        body = {
            "data": [
                {
                    "id": "wf-1",
                    "user_id": "u",
                    "name": "Alpha",
                    "description": None,
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-01T00:00:00Z",
                    "runs_count": 2,
                    "last_run_at": None,
                    "last_run_status": "completed",
                }
            ],
            "meta": _META,
            "pagination": {"next": None, "prev": None, "limit": 50, "total": 1},
        }
        respx.get(f"{_BASE}/api/v1/workflows").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["workflows", "list", "--json"])
        assert result.exit_code == 0, result.output
        assert '"id": "wf-1"' in result.output


class TestDataMode:
    @respx.mock
    def test_workflows_show(self, tmp_home) -> None:
        body = {
            "data": {
                "id": "wf-1",
                "user_id": "u",
                "name": "Alpha",
                "description": "d",
                "definition": {"graph": {"nodes": [], "edges": []}, "execution": {}},
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "runs_count": 2,
                "last_run_at": None,
                "last_run_status": "completed",
            },
            "meta": _META,
        }
        respx.get(f"{_BASE}/api/v1/workflows/wf-1").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["workflows", "show", "wf-1", "--json"])
        assert result.exit_code == 0, result.output
        assert '"name": "Alpha"' in result.output


class TestListMode:
    @respx.mock
    def test_workspace_list(self, tmp_home) -> None:
        body = {
            "data": [
                {
                    "id": "ws-1",
                    "name": "Main",
                    "slug": "main",
                    "color_idx": 0,
                    "created_by": "u",
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-01T00:00:00Z",
                }
            ],
            "meta": _META,
            "pagination": {"next": None, "prev": None, "limit": 50, "total": 1},
        }
        respx.get(f"{_BASE}/api/v1/workspaces").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["workspace", "list", "--json"])
        assert result.exit_code == 0, result.output
        assert '"id": "ws-1"' in result.output


class TestActionMode:
    @respx.mock
    def test_workflows_delete(self, tmp_home) -> None:
        body = {"data": {"deleted": True}, "meta": _META}
        respx.delete(f"{_BASE}/api/v1/workflows/wf-1").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["workflows", "delete", "wf-1", "--yes", "--json"])
        assert result.exit_code == 0, result.output
        assert '"ok": true' in result.output


class TestErrorEnvelope:
    @respx.mock
    def test_404_maps_to_structured_error(self, tmp_home) -> None:
        body = {"error": {"code": "NOT_FOUND", "message": "Workflow not found."}, "meta": _META}
        respx.get(f"{_BASE}/api/v1/workflows/wf-x").mock(return_value=httpx.Response(404, json=body))
        result = _invoke(["workflows", "show", "wf-x", "--json"])
        assert result.exit_code == 1
        assert '"code": "NOT_FOUND"' in result.output
        assert "request_id" in result.output

    @respx.mock
    def test_404_plain_text_error(self, tmp_home) -> None:
        body = {"error": {"code": "NOT_FOUND", "message": "Workflow not found."}, "meta": _META}
        respx.get(f"{_BASE}/api/v1/workflows/wf-x").mock(return_value=httpx.Response(404, json=body))
        result = _invoke(["workflows", "show", "wf-x"])
        assert result.exit_code == 1
        assert "[NOT_FOUND]" in result.output
        assert "Workflow not found." in result.output
