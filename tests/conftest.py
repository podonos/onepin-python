"""Test fixtures: tmp HOME, respx, sample envelopes."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _reset_cli_state():
    """Isolate process-local CLI state + the NO_COLOR env var between tests.

    Import is guarded: the build-artifact tests (``tests/build/``) run in the publish
    workflow's build job, which installs only build tooling -- ``onepin`` is not importable
    there. The state reset is a no-op in that environment.
    """
    try:
        from onepin._cli import _state
    except ModuleNotFoundError:
        yield
        return

    _state.root_options = {}
    os.environ.pop("NO_COLOR", None)
    yield
    _state.root_options = {}
    os.environ.pop("NO_COLOR", None)


@pytest.fixture
def tmp_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("HOME", str(tmp_path))
    if os.name != "nt":
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
    return tmp_path


@pytest.fixture
def sample_workflow_envelope() -> dict:
    return {
        "data": {
            "id": "wf-00000000-0000-0000-0000-000000000001",
            "name": "Test Workflow",
            "status": "active",
            "created_at": "2025-01-01T00:00:00Z",
        },
        "meta": {"request_id": "01JTEST00000000000000000000", "timestamp": "2025-01-01T00:00:00Z"},
    }


@pytest.fixture
def sample_voice_envelope() -> dict:
    return {
        "data": {
            "id": "v-00000000-0000-0000-0000-000000000001",
            "name": "Test Voice",
            "locale": "en-US",
            "provider": "elevenlabs",
        },
        "meta": {"request_id": "01JTEST00000000000000000000", "timestamp": "2025-01-01T00:00:00Z"},
    }


@pytest.fixture
def sample_template_envelope() -> dict:
    return {
        "data": {
            "id": "tmpl-00000000-0000-0000-0000-000000000001",
            "name": "Test Template",
            "description": "A test template",
            "published_at": "2025-01-01T00:00:00Z",
        },
        "meta": {"request_id": "01JTEST00000000000000000000", "timestamp": "2025-01-01T00:00:00Z"},
    }


@pytest.fixture
def sample_upload_envelope() -> dict:
    return {
        "data": {
            "upload": {
                "id": "upl-00000000-0000-0000-0000-000000000001",
                "filename": "script.txt",
                "category": "script",
                "status": "pending",
            },
            "upload_url": "https://s3.example.com/presigned?sig=abc",
        },
        "meta": {"request_id": "01JTEST00000000000000000000", "timestamp": "2025-01-01T00:00:00Z"},
    }
