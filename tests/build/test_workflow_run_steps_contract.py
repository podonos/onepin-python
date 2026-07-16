"""Generated SDK contract coverage for lightweight workflow run steps."""

from __future__ import annotations

import inspect

import httpx
import pytest
import respx

from onepin.client import AsyncOnePinClient, OnePinClient
from onepin.types import WorkflowRunStepOut
from onepin.workflows.runs.client import AsyncRunsClient, RunsClient
from onepin.workflows.runs.raw_client import AsyncRawRunsClient, RawRunsClient

_BASE = "https://api.onepin.ai"
_STEPS_URL = f"{_BASE}/api/v1/workflows/wf-1/runs/run-1/steps"
_META = {"request_id": "req-1", "timestamp": "2025-01-01T00:00:00Z"}
_STEP = {
    "id": "step-1",
    "node_id": "node-1",
    "node_type": "validator_error_rate",
    "node_display_name": "Error Rate",
    "status": "completed",
    "iteration": 0,
    "started_at": "2025-01-01T00:00:00Z",
    "completed_at": "2025-01-01T00:00:01Z",
    "result": None,
    "has_result": True,
    "active_ports": ["output"],
    "error": None,
}
_FILTER_CASES = [
    ({}, {}),
    ({"include_result": True}, {"include_result": "true"}),
    ({"node_type": "validator_error_rate"}, {"node_type": "validator_error_rate"}),
    ({"node_id": "node-1"}, {"node_id": "node-1"}),
    (
        {"include_result": True, "node_type": "validator_error_rate", "node_id": "node-1"},
        {"include_result": "true", "node_type": "validator_error_rate", "node_id": "node-1"},
    ),
]


@pytest.mark.parametrize("client_type", [RunsClient, AsyncRunsClient, RawRunsClient, AsyncRawRunsClient])
def test_all_generated_surfaces_expose_optional_step_filters(client_type: type[object]) -> None:
    signature = inspect.signature(client_type.steps)

    assert tuple(signature.parameters) == (
        "self",
        "workflow_id",
        "run_id",
        "include_result",
        "node_type",
        "node_id",
        "workspace_id",
        "request_options",
    )
    for name in ("include_result", "node_type", "node_id"):
        assert signature.parameters[name].default is None


def test_generated_step_model_exposes_lightweight_result_metadata() -> None:
    step = WorkflowRunStepOut.model_validate(_STEP)

    assert step.result is None
    assert step.has_result is True
    assert step.active_ports == ["output"]


def test_generated_step_model_accepts_older_backend_payload() -> None:
    legacy_payload = {key: value for key, value in _STEP.items() if key not in {"has_result", "active_ports"}}
    legacy_payload["result"] = {"output": "legacy full result"}

    step = WorkflowRunStepOut.model_validate(legacy_payload)

    assert step.result == {"output": "legacy full result"}
    assert step.has_result is None
    assert step.active_ports is None


@pytest.mark.parametrize("raw", [False, True], ids=["standard", "raw"])
@pytest.mark.parametrize(("kwargs", "expected_query"), _FILTER_CASES)
@respx.mock
def test_generated_sync_clients_serialize_step_filters(
    raw: bool, kwargs: dict[str, object], expected_query: dict[str, str]
) -> None:
    route = respx.get(_STEPS_URL).mock(return_value=httpx.Response(200, json={"data": [_STEP], "meta": _META}))
    http_client = httpx.Client()
    client = OnePinClient(token="op_live_test", httpx_client=http_client)
    try:
        runs = client.workflows.runs.with_raw_response if raw else client.workflows.runs
        response = runs.steps("wf-1", "run-1", **kwargs)
    finally:
        http_client.close()

    data = response.data.data if raw else response.data
    assert data[0].has_result is True
    assert dict(route.calls[0].request.url.params) == expected_query


@pytest.mark.asyncio
@pytest.mark.parametrize("raw", [False, True], ids=["standard", "raw"])
@pytest.mark.parametrize(("kwargs", "expected_query"), _FILTER_CASES)
@respx.mock
async def test_generated_async_clients_serialize_step_filters(
    raw: bool, kwargs: dict[str, object], expected_query: dict[str, str]
) -> None:
    route = respx.get(_STEPS_URL).mock(return_value=httpx.Response(200, json={"data": [_STEP], "meta": _META}))
    http_client = httpx.AsyncClient()
    client = AsyncOnePinClient(token="op_live_test", httpx_client=http_client)
    try:
        runs = client.workflows.runs.with_raw_response if raw else client.workflows.runs
        response = await runs.steps("wf-1", "run-1", **kwargs)
    finally:
        await http_client.aclose()

    data = response.data.data if raw else response.data
    assert data[0].active_ports == ["output"]
    assert dict(route.calls[0].request.url.params) == expected_query
