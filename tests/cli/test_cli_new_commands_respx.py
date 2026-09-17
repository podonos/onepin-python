"""respx integration tests for the 16 new table-driven CLI commands.

Exercises providers, account, workflows runs (outputs/analysis/pause/resume),
templates estimate, and workflows validate end-to-end through the real SDK
serialization path.
"""

from __future__ import annotations

import json
import tempfile

import httpx
import respx
from typer.testing import CliRunner

from onepin._cli.main import app

runner = CliRunner()
_BASE = "https://api.onepin.ai"
_META = {"request_id": "01JTEST00000000000000000000", "timestamp": "2025-01-01T00:00:00Z"}


def _invoke(argv: list[str]):
    return runner.invoke(app, ["--api-key", "op_live_x", *argv])


def _invoke_with_workspace(argv: list[str]):
    return runner.invoke(app, ["--api-key", "op_live_x", "--workspace", "ws-99", *argv])


# ---------------------------------------------------------------------------
# Shared response fixtures: minimally valid bodies for complex SDK models
# ---------------------------------------------------------------------------

_BALANCE_DATA = {
    "balance": 1500,
    "plan_grant": 2000,
    "plan_tier": "paid",
    "remaining": 1500,
}

_PLAN_LIMITS_DATA = {
    "monthly_credits": 2000,
    "workspaces_per_owner": 5,
    "concurrent_runs_per_user": 3,
    "storage_bytes_per_workspace": 5368709120,
}

_NOTIFICATION_PREFS_DATA = {
    "completed_generation_email": True,
    "failed_generation_email": False,
}

_RUN_OUT_DATA = {
    "id": "run-1",
    "workflow_id": "wf-1",
    "status": "paused",
    "run_number": 1,
    "token_cost": 0,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
}

_RUN_OUTPUTS_DATA = {
    "run_id": "run-1",
    "run_status": "completed",
    "outputs": [
        {
            "node_id": "sink-1",
            "node_type": "operator_sink",
            "display_name": "Sink",
            "status": "completed",
            "lines": [],
            "line_count": 0,
            "truncated": False,
        }
    ],
}

_RUN_ANALYSIS_DATA = {
    "run": {"id": "run-1", "status": "completed"},
    "audio": {"status": "ok"},
    "credits": {"status": "settled"},
}

_VALIDATE_DATA = {
    "valid": True,
    "summary": {},
    "errors": [],
    "blocked": [],
}

_TEMPLATE_ESTIMATE_DATA = {
    "unit_chars": 1000,
    "variable_min_credits_per_unit": 1,
    "variable_expected_credits_per_unit": 2,
    "variable_max_credits_per_unit": 3,
    "fixed_min_credits": 0,
    "fixed_expected_credits": 0,
    "fixed_max_credits": 0,
    "total_min_credits_per_unit": 1,
    "total_expected_credits_per_unit": 2,
    "total_max_credits_per_unit": 3,
    "breakdown": [],
    "source_snapshot": "draft",
    "source_node_ids": [],
    "definition_fingerprint": "abc123",
    "rate_fingerprint": "def456",
    "cache_status": "hit",
    "computed_at": "2025-01-01T00:00:00Z",
}

_CATALOG_VOICE = {
    "id": "v-1",
    "provider_voice_id": "pv-1",
    "name": "Alice",
    "gender": "female",
    "age": "adult",
    "accent": "american",
}


_TEMPLATE_OUT = {
    "id": "tmpl-1",
    "name": "My Media Template",
    "category": "media",
    "definition": {},
    "is_starter": False,
    "is_public": False,
    "is_favorite": True,
    "uses_count": 5,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
}

# ---------------------------------------------------------------------------
# Providers group
# ---------------------------------------------------------------------------


class TestProvidersGroup:
    @respx.mock
    def test_providers_list_table(self, tmp_home) -> None:
        body = {
            "data": [
                {
                    "provider": "elevenlabs",
                    "display_name": "ElevenLabs",
                    "kind": "tts",
                    "model_count": 3,
                    "beta": False,
                }
            ],
            "meta": _META,
            "pagination": {"next": None, "prev": None, "limit": 50},
        }
        respx.get(f"{_BASE}/api/v1/providers").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["providers", "list"])
        assert result.exit_code == 0, result.output
        assert "elevenlabs" in result.output

    @respx.mock
    def test_providers_list_json(self, tmp_home) -> None:
        body = {
            "data": [
                {
                    "provider": "elevenlabs",
                    "display_name": "ElevenLabs",
                    "kind": "tts",
                    "model_count": 3,
                    "beta": False,
                }
            ],
            "meta": _META,
            "pagination": {"next": None, "prev": None, "limit": 50},
        }
        respx.get(f"{_BASE}/api/v1/providers").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["providers", "list", "--json"])
        assert result.exit_code == 0, result.output
        assert '"provider": "elevenlabs"' in result.output

    @respx.mock
    def test_providers_show(self, tmp_home) -> None:
        body = {
            "data": {
                "provider": "elevenlabs",
                "display_name": "ElevenLabs",
                "kind": "tts",
                "model_count": 3,
                "beta": False,
            },
            "meta": _META,
        }
        respx.get(f"{_BASE}/api/v1/providers/elevenlabs").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["providers", "show", "elevenlabs", "--json"])
        assert result.exit_code == 0, result.output
        assert '"provider": "elevenlabs"' in result.output

    @respx.mock
    def test_providers_models_list_table(self, tmp_home) -> None:
        body = {
            "data": [
                {
                    "model": "eleven_multilingual_v2",
                    "display_name": "Multilingual v2",
                    "content_type": "audio/mpeg",
                    "voice_count": 42,
                    "beta": False,
                }
            ],
            "meta": _META,
            "pagination": {"next": None, "prev": None, "limit": 50},
        }
        respx.get(f"{_BASE}/api/v1/providers/elevenlabs/models").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["providers", "models", "list", "elevenlabs"])
        assert result.exit_code == 0, result.output
        assert "eleven_multilingual_v2" in result.output

    @respx.mock
    def test_providers_models_list_json(self, tmp_home) -> None:
        body = {
            "data": [
                {"model": "m1", "display_name": "M1", "content_type": "audio/mpeg", "voice_count": 5, "beta": False}
            ],
            "meta": _META,
            "pagination": {"next": None, "prev": None, "limit": 50},
        }
        respx.get(f"{_BASE}/api/v1/providers/elevenlabs/models").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["providers", "models", "list", "elevenlabs", "--json"])
        assert result.exit_code == 0, result.output
        assert '"model": "m1"' in result.output

    @respx.mock
    def test_providers_models_show(self, tmp_home) -> None:
        body = {
            "data": {
                "model": "eleven_multilingual_v2",
                "display_name": "Multilingual v2",
                "content_type": "audio/mpeg",
                "voice_count": 42,
                "beta": False,
            },
            "meta": _META,
        }
        respx.get(f"{_BASE}/api/v1/providers/elevenlabs/models/eleven_multilingual_v2").mock(
            return_value=httpx.Response(200, json=body)
        )
        result = _invoke(["providers", "models", "show", "elevenlabs", "eleven_multilingual_v2", "--json"])
        assert result.exit_code == 0, result.output
        assert '"model": "eleven_multilingual_v2"' in result.output

    @respx.mock
    def test_providers_models_voices_pager_footer(self, tmp_home) -> None:
        """pagination.total drives the exact 'Showing X of N' footer."""
        body = {
            "data": [_CATALOG_VOICE, {**_CATALOG_VOICE, "id": "v-2", "provider_voice_id": "pv-2", "name": "Bob"}],
            "meta": _META,
            "pagination": {"total": 100, "limit": 50},
        }
        respx.get(f"{_BASE}/api/v1/providers/elevenlabs/models/eleven_multilingual_v2/voices").mock(
            return_value=httpx.Response(200, json=body)
        )
        result = _invoke(["providers", "models", "voices", "elevenlabs", "eleven_multilingual_v2"])
        assert result.exit_code == 0, result.output
        assert "Showing 2 of 100" in result.output

    @respx.mock
    def test_providers_models_voices_json(self, tmp_home) -> None:
        body = {
            "data": [_CATALOG_VOICE],
            "meta": _META,
            "pagination": {"total": 1, "limit": 50},
        }
        respx.get(f"{_BASE}/api/v1/providers/elevenlabs/models/eleven_multilingual_v2/voices").mock(
            return_value=httpx.Response(200, json=body)
        )
        result = _invoke(["providers", "models", "voices", "elevenlabs", "eleven_multilingual_v2", "--json"])
        assert result.exit_code == 0, result.output
        assert '"id": "v-1"' in result.output
        # JSON mode: no pager footer
        assert "Showing" not in result.output


# ---------------------------------------------------------------------------
# Account group
# ---------------------------------------------------------------------------


class TestAccountGroup:
    @respx.mock
    def test_account_credits_json(self, tmp_home) -> None:
        body = {"data": _BALANCE_DATA, "meta": _META}
        respx.get(f"{_BASE}/api/v1/users/me/credits").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["account", "credits", "--json"])
        assert result.exit_code == 0, result.output
        assert '"balance": 1500' in result.output

    @respx.mock
    def test_account_credits_no_workspace_param(self, tmp_home) -> None:
        """Even with --workspace globally, credits endpoint must not send workspace_id."""
        route = respx.get(f"{_BASE}/api/v1/users/me/credits").mock(
            return_value=httpx.Response(200, json={"data": _BALANCE_DATA, "meta": _META})
        )
        result = _invoke_with_workspace(["account", "credits", "--json"])
        assert result.exit_code == 0, result.output
        # Workspace must not appear in the query params
        assert "workspace_id" not in str(route.calls.last.request.url)

    @respx.mock
    def test_account_plan_json(self, tmp_home) -> None:
        body = {"data": _PLAN_LIMITS_DATA, "meta": _META}
        respx.get(f"{_BASE}/api/v1/users/me/limits").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["account", "plan", "--json"])
        assert result.exit_code == 0, result.output
        assert '"monthly_credits": 2000' in result.output

    @respx.mock
    def test_account_plan_no_workspace_param(self, tmp_home) -> None:
        """Even with --workspace globally, plan endpoint must not send workspace_id."""
        route = respx.get(f"{_BASE}/api/v1/users/me/limits").mock(
            return_value=httpx.Response(200, json={"data": _PLAN_LIMITS_DATA, "meta": _META})
        )
        result = _invoke_with_workspace(["account", "plan", "--json"])
        assert result.exit_code == 0, result.output
        assert "workspace_id" not in str(route.calls.last.request.url)

    @respx.mock
    def test_account_notifications_show_json(self, tmp_home) -> None:
        body = {"data": _NOTIFICATION_PREFS_DATA, "meta": _META}
        respx.get(f"{_BASE}/api/v1/users/me/notification-preferences").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["account", "notifications", "show", "--json"])
        assert result.exit_code == 0, result.output
        assert '"completed_generation_email": true' in result.output

    @respx.mock
    def test_account_notifications_set_explicit_false(self, tmp_home) -> None:
        """--no-completed-generation-email must send completed_generation_email: false in body."""
        route = respx.patch(f"{_BASE}/api/v1/users/me/notification-preferences").mock(
            return_value=httpx.Response(
                200,
                json={"data": {**_NOTIFICATION_PREFS_DATA, "completed_generation_email": False}, "meta": _META},
            )
        )
        result = _invoke(["account", "notifications", "set", "--no-completed-generation-email", "--json"])
        assert result.exit_code == 0, result.output
        sent = json.loads(route.calls.last.request.content)
        # Tri-state: False must be forwarded (not dropped at its default)
        assert sent.get("completed_generation_email") is False

    @respx.mock
    def test_account_notifications_set_no_flags_empty_body(self, tmp_home) -> None:
        """Passing no flags sends an empty patch body, leaving preferences unchanged."""
        route = respx.patch(f"{_BASE}/api/v1/users/me/notification-preferences").mock(
            return_value=httpx.Response(200, json={"data": _NOTIFICATION_PREFS_DATA, "meta": _META})
        )
        result = _invoke(["account", "notifications", "set", "--json"])
        assert result.exit_code == 0, result.output
        sent = json.loads(route.calls.last.request.content)
        assert "completed_generation_email" not in sent
        assert "failed_generation_email" not in sent

    @respx.mock
    def test_account_notifications_no_workspace_param(self, tmp_home) -> None:
        """Notification endpoints are caller-scoped, not workspace-scoped."""
        route = respx.get(f"{_BASE}/api/v1/users/me/notification-preferences").mock(
            return_value=httpx.Response(200, json={"data": _NOTIFICATION_PREFS_DATA, "meta": _META})
        )
        result = _invoke_with_workspace(["account", "notifications", "show", "--json"])
        assert result.exit_code == 0, result.output
        assert "workspace_id" not in str(route.calls.last.request.url)

    @respx.mock
    def test_account_templates_filter_forwarding(self, tmp_home) -> None:
        """--category, --sort, --favorites-only are forwarded to the SDK."""
        route = respx.get(f"{_BASE}/api/v1/users/me/templates").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [_TEMPLATE_OUT],
                    "meta": _META,
                    "pagination": {"next": None, "prev": None, "limit": 50},
                },
            )
        )
        result = _invoke(["account", "templates", "--category", "media", "--sort", "recent", "--favorites-only"])
        assert result.exit_code == 0, result.output
        url_str = str(route.calls.last.request.url)
        assert "category=media" in url_str
        assert "sort=recent" in url_str
        assert "favorites_only=true" in url_str

    @respx.mock
    def test_account_templates_json(self, tmp_home) -> None:
        body = {
            "data": [_TEMPLATE_OUT],
            "meta": _META,
            "pagination": {"next": None, "prev": None, "limit": 50},
        }
        respx.get(f"{_BASE}/api/v1/users/me/templates").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["account", "templates", "--json"])
        assert result.exit_code == 0, result.output
        assert '"id": "tmpl-1"' in result.output


# ---------------------------------------------------------------------------
# Workflows runs: outputs, analysis, pause, resume
# ---------------------------------------------------------------------------


class TestWorkflowRunsNewCommands:
    @respx.mock
    def test_runs_outputs_json(self, tmp_home) -> None:
        body = {"data": _RUN_OUTPUTS_DATA, "meta": _META}
        respx.get(f"{_BASE}/api/v1/workflows/wf-1/runs/run-1/outputs").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["workflows", "runs", "outputs", "wf-1", "run-1", "--json"])
        assert result.exit_code == 0, result.output
        assert '"run_id": "run-1"' in result.output

    @respx.mock
    def test_runs_analysis_json(self, tmp_home) -> None:
        body = {"data": _RUN_ANALYSIS_DATA, "meta": _META}
        respx.get(f"{_BASE}/api/v1/workflows/wf-1/runs/run-1/analysis").mock(
            return_value=httpx.Response(200, json=body)
        )
        result = _invoke(["workflows", "runs", "analysis", "wf-1", "run-1", "--json"])
        assert result.exit_code == 0, result.output
        assert '"status": "completed"' in result.output

    @respx.mock
    def test_runs_pause_success_message(self, tmp_home) -> None:
        body = {"data": _RUN_OUT_DATA, "meta": _META}
        respx.post(f"{_BASE}/api/v1/workflows/wf-1/runs/run-1/pause").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["workflows", "runs", "pause", "wf-1", "run-1"])
        assert result.exit_code == 0, result.output
        assert "Paused run run-1" in result.output

    @respx.mock
    def test_runs_pause_json(self, tmp_home) -> None:
        body = {"data": _RUN_OUT_DATA, "meta": _META}
        respx.post(f"{_BASE}/api/v1/workflows/wf-1/runs/run-1/pause").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["workflows", "runs", "pause", "wf-1", "run-1", "--json"])
        assert result.exit_code == 0, result.output
        assert '"ok": true' in result.output

    @respx.mock
    def test_runs_resume_success_message(self, tmp_home) -> None:
        body = {"data": {**_RUN_OUT_DATA, "status": "running"}, "meta": _META}
        respx.post(f"{_BASE}/api/v1/workflows/wf-1/runs/run-1/resume").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["workflows", "runs", "resume", "wf-1", "run-1"])
        assert result.exit_code == 0, result.output
        assert "Resumed run run-1" in result.output

    @respx.mock
    def test_runs_resume_json(self, tmp_home) -> None:
        body = {"data": {**_RUN_OUT_DATA, "status": "running"}, "meta": _META}
        respx.post(f"{_BASE}/api/v1/workflows/wf-1/runs/run-1/resume").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["workflows", "runs", "resume", "wf-1", "run-1", "--json"])
        assert result.exit_code == 0, result.output
        assert '"ok": true' in result.output


# ---------------------------------------------------------------------------
# Templates estimate
# ---------------------------------------------------------------------------


class TestTemplatesEstimate:
    @respx.mock
    def test_templates_estimate_json(self, tmp_home) -> None:
        body = {"data": _TEMPLATE_ESTIMATE_DATA, "meta": _META}
        respx.get(f"{_BASE}/api/v1/templates/tmpl-1/estimate").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["templates", "estimate", "tmpl-1", "--json"])
        assert result.exit_code == 0, result.output
        assert '"cache_status": "hit"' in result.output


# ---------------------------------------------------------------------------
# Workflows validate
# ---------------------------------------------------------------------------

_VALID_DEFINITION = {"graph": {"nodes": [], "edges": []}, "execution": {}}


class TestWorkflowsValidate:
    @respx.mock
    def test_validate_inline_json(self, tmp_home) -> None:
        body = {"data": _VALIDATE_DATA, "meta": _META}
        respx.post(f"{_BASE}/api/v1/workflows/validate").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["workflows", "validate", "--definition", json.dumps(_VALID_DEFINITION)])
        assert result.exit_code == 0, result.output

    @respx.mock
    def test_validate_file_reference(self, tmp_home) -> None:
        body = {"data": _VALIDATE_DATA, "meta": _META}
        route = respx.post(f"{_BASE}/api/v1/workflows/validate").mock(return_value=httpx.Response(200, json=body))
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fh:
            json.dump(_VALID_DEFINITION, fh)
            fpath = fh.name
        result = _invoke(["workflows", "validate", "--definition", f"@{fpath}"])
        assert result.exit_code == 0, result.output
        # The file was read and the definition was sent in the request body
        sent = json.loads(route.calls.last.request.content)
        assert "definition" in sent

    @respx.mock
    def test_validate_json_output(self, tmp_home) -> None:
        body = {
            "data": {
                **_VALIDATE_DATA,
                "valid": False,
                "errors": [{"code": "MISSING_SINK", "rule": "missing_sink", "message": "Missing sink node."}],
            },
            "meta": _META,
        }
        respx.post(f"{_BASE}/api/v1/workflows/validate").mock(return_value=httpx.Response(200, json=body))
        result = _invoke(["workflows", "validate", "--definition", json.dumps(_VALID_DEFINITION), "--json"])
        assert result.exit_code == 0, result.output
        assert '"valid": false' in result.output

    def test_validate_malformed_json(self, tmp_home) -> None:
        """Malformed JSON produces a clean INVALID_JSON error before any HTTP call."""
        result = _invoke(["workflows", "validate", "--definition", "{not valid json"])
        assert result.exit_code == 1
        assert "INVALID_JSON" in result.output
