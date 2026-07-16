"""CLI-level tests for table-driven commands via a fake client (monkeypatched get_client).

Covers, per representative command: happy path, ``--json``, not-authenticated, and an
``ApiError 404``. The dispatcher is exercised through the real Typer app + CliRunner.
"""

from __future__ import annotations

import datetime as dt

import pytest
from typer.testing import CliRunner

from onepin._cli import _dispatch
from onepin._cli.main import app
from onepin.core.api_error import ApiError
from onepin.core.pagination import SyncPager
from onepin.errors import NotFoundError

runner = CliRunner()
NOW = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)


def _pager(items: list) -> SyncPager:
    return SyncPager(get_next=None, has_next=False, items=items, response=None)


def _workflow_item():
    from onepin.types import WorkflowListItem

    return WorkflowListItem(
        id="wf-1",
        user_id="u",
        name="Alpha",
        description=None,
        created_at=NOW,
        updated_at=NOW,
        runs_count=2,
        last_run_at=None,
        last_run_status="completed",
    )


def _workflow_out():
    from onepin.types import ApiResponseWorkflowOut, WorkflowOut

    wf = WorkflowOut(
        id="wf-1",
        user_id="u",
        name="Alpha",
        description="d",
        definition={"graph": {"nodes": [], "edges": []}, "execution": {}},
        created_at=NOW,
        updated_at=NOW,
        runs_count=2,
        last_run_at=None,
        last_run_status="completed",
    )
    return ApiResponseWorkflowOut(data=wf, meta=_meta())


def _dict_response(**data):
    from onepin.types import ApiResponseDict

    return ApiResponseDict(data=data, meta=_meta())


def _meta():
    from onepin.types.meta import Meta

    return Meta(request_id="req-1", timestamp=NOW)


class FakeRuns:
    raise_404 = False

    def __init__(self) -> None:
        self.step_calls: list[dict[str, object]] = []

    def cancel(self, workflow_id, run_id, **kw):
        if self.raise_404:
            raise NotFoundError(body={"error": {"code": "NOT_FOUND", "message": "gone"}})
        return _dict_response(cancelled=True, id=run_id)

    def steps(self, workflow_id, run_id, **kw):
        self.step_calls.append({"workflow_id": workflow_id, "run_id": run_id, **kw})
        return [{"id": "step-1", "node_id": "node-1", "status": "completed"}]


class FakeWorkflows:
    raise_404 = False

    def __init__(self) -> None:
        self.runs = FakeRuns()

    def list(self, **kw):
        return _pager([_workflow_item()])

    def get(self, workflow_id, **kw):
        if self.raise_404:
            raise NotFoundError(body={"error": {"code": "NOT_FOUND", "message": "gone"}})
        return _workflow_out()

    def delete_workflow(self, workflow_id, **kw):
        if self.raise_404:
            raise NotFoundError(body={"error": {"code": "NOT_FOUND", "message": "gone"}})
        return _dict_response(deleted=True, id=workflow_id)


class FakeClient:
    def __init__(self) -> None:
        self.workflows = FakeWorkflows()


@pytest.fixture
def fake_client(monkeypatch: pytest.MonkeyPatch) -> FakeClient:
    client = FakeClient()
    monkeypatch.setattr(_dispatch, "get_client", lambda: client)
    return client


def _invoke(argv: list[str], *, key: bool = True):
    prefix = ["--api-key", "op_live_x"] if key else []
    return runner.invoke(app, [*prefix, *argv])


class TestPagerMode:
    def test_happy(self, fake_client: FakeClient, tmp_home) -> None:
        result = _invoke(["--no-color", "workflows", "list"])
        assert result.exit_code == 0, result.output
        assert "Alpha" in result.output

    def test_json(self, fake_client: FakeClient, tmp_home) -> None:
        result = _invoke(["workflows", "list", "--json"])
        assert result.exit_code == 0, result.output
        assert '"id": "wf-1"' in result.output


class TestDataMode:
    def test_happy(self, fake_client: FakeClient, tmp_home) -> None:
        result = _invoke(["--no-color", "workflows", "show", "wf-1"])
        assert result.exit_code == 0, result.output
        assert "Alpha" in result.output

    def test_json(self, fake_client: FakeClient, tmp_home) -> None:
        result = _invoke(["workflows", "show", "wf-1", "--json"])
        assert result.exit_code == 0, result.output
        assert '"name": "Alpha"' in result.output

    def test_not_found_maps_to_exit_1(self, fake_client: FakeClient, tmp_home) -> None:
        fake_client.workflows.raise_404 = True
        result = _invoke(["workflows", "show", "wf-1"])
        assert result.exit_code == 1
        assert "NOT_FOUND" in result.output


class TestActionMode:
    def test_delete_text(self, fake_client: FakeClient, tmp_home) -> None:
        result = _invoke(["workflows", "delete", "wf-1", "--yes"])
        assert result.exit_code == 0, result.output
        assert "Deleted workflow wf-1" in result.output

    def test_delete_json(self, fake_client: FakeClient, tmp_home) -> None:
        result = _invoke(["workflows", "delete", "wf-1", "--yes", "--json"])
        assert result.exit_code == 0, result.output
        assert '"ok": true' in result.output

    def test_delete_404_idempotent_under_yes(self, fake_client: FakeClient, tmp_home) -> None:
        fake_client.workflows.raise_404 = True
        result = _invoke(["workflows", "delete", "wf-1", "--yes"])
        assert result.exit_code == 0, result.output
        assert "Deleted workflow wf-1" in result.output


class TestNonDeleteDestructive404:
    """Idempotent-404 is delete-only. cancel/remove/revoke must surface 404, not fake success."""

    def test_cancel_404_under_yes_surfaces_error(self, fake_client: FakeClient, tmp_home) -> None:
        fake_client.workflows.runs.raise_404 = True
        result = _invoke(["workflows", "runs", "cancel", "wf-1", "run-x", "--yes"])
        assert result.exit_code == 1, result.output
        assert "NOT_FOUND" in result.output
        assert "cancelled" not in result.output.lower()


class TestWorkflowRunSteps:
    def test_omits_optional_filters_by_default(self, fake_client: FakeClient, tmp_home) -> None:
        result = _invoke(["workflows", "runs", "steps", "wf-1", "run-1", "--json"])

        assert result.exit_code == 0, result.output
        assert fake_client.workflows.runs.step_calls == [{"workflow_id": "wf-1", "run_id": "run-1"}]
        assert '"id": "step-1"' in result.output

    @pytest.mark.parametrize(
        ("flag", "value", "expected"),
        [
            ("--include-result", None, {"include_result": True}),
            ("--node-type", "operator_generator", {"node_type": "operator_generator"}),
            ("--node-id", "node-7", {"node_id": "node-7"}),
        ],
    )
    def test_forwards_each_optional_filter(
        self,
        fake_client: FakeClient,
        tmp_home,
        flag: str,
        value: str | None,
        expected: dict[str, object],
    ) -> None:
        option = [flag] if value is None else [flag, value]
        result = _invoke(["workflows", "runs", "steps", "wf-1", "run-1", *option, "--json"])

        assert result.exit_code == 0, result.output
        assert fake_client.workflows.runs.step_calls == [{"workflow_id": "wf-1", "run_id": "run-1", **expected}]

    def test_forwards_combined_filters(self, fake_client: FakeClient, tmp_home) -> None:
        result = _invoke(
            [
                "workflows",
                "runs",
                "steps",
                "wf-1",
                "run-1",
                "--include-result",
                "--node-type",
                "validator_error_rate",
                "--node-id",
                "node-7",
                "--json",
            ]
        )

        assert result.exit_code == 0, result.output
        assert fake_client.workflows.runs.step_calls == [
            {
                "workflow_id": "wf-1",
                "run_id": "run-1",
                "include_result": True,
                "node_type": "validator_error_rate",
                "node_id": "node-7",
            }
        ]

    def test_node_type_rejects_unknown_value(self, fake_client: FakeClient, tmp_home) -> None:
        result = _invoke(["workflows", "runs", "steps", "wf-1", "run-1", "--node-type", "not-a-node", "--json"])

        assert result.exit_code == 2
        assert fake_client.workflows.runs.step_calls == []


class TestNotAuthenticated:
    def test_no_creds_exit_1(self, tmp_home) -> None:
        # No flag, no env, no file -> get_client raises OnePinAuthError.
        result = runner.invoke(app, ["workflows", "list"])
        assert result.exit_code == 1
        assert "NOT_AUTHENTICATED" in result.output

    def test_no_creds_json(self, tmp_home) -> None:
        result = runner.invoke(app, ["workflows", "list", "--json"])
        assert result.exit_code == 1
        assert '"code": "NOT_AUTHENTICATED"' in result.output


class TestDestructiveConfirm:
    def test_delete_without_yes_aborts(self, fake_client: FakeClient, tmp_home) -> None:
        # No --yes, no input -> confirm aborts (exit 1) and never calls the SDK.
        result = runner.invoke(app, ["--api-key", "op_live_x", "workflows", "delete", "wf-1"], input="n\n")
        assert result.exit_code == 1

    def test_delete_confirm_yes_proceeds(self, fake_client: FakeClient, tmp_home) -> None:
        result = runner.invoke(app, ["--api-key", "op_live_x", "workflows", "delete", "wf-1"], input="y\n")
        assert result.exit_code == 0, result.output
        assert "Deleted workflow wf-1" in result.output

    def test_delete_json_without_yes_returns_structured_error(self, fake_client: FakeClient, tmp_home) -> None:
        """--json without --yes must NOT prompt; must emit JSON error envelope + exit 1."""
        result = _invoke(["--json", "workflows", "delete", "wf-1"])
        assert result.exit_code == 1
        # stdout must be empty (no prompt text corrupting the machine-readable contract)

        # CliRunner mixes stdout/stderr; check the output contains the structured error
        assert "CONFIRMATION_REQUIRED" in result.output
        assert "Pass --yes" in result.output


class TestLimitValidation:
    def test_limit_zero_is_usage_error(self, fake_client: FakeClient, tmp_home) -> None:
        result = _invoke(["workflows", "list", "--limit", "0"])
        assert result.exit_code == 2


class TestApiErrorMapping:
    def test_generic_api_error(self, fake_client: FakeClient, tmp_home, monkeypatch) -> None:
        def boom(workflow_id, **kw):
            raise ApiError(status_code=500, body={"error": {"code": "SERVER_ERROR", "message": "boom"}})

        monkeypatch.setattr(fake_client.workflows, "get", boom)
        result = _invoke(["workflows", "show", "wf-1"])
        assert result.exit_code == 1
        assert "SERVER_ERROR" in result.output
