"""Tests for the render module."""
from __future__ import annotations

import json
import os
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from onepin._cli import render


class TestRenderJson:
    def test_emits_json_to_stdout(self, capsys: pytest.CaptureFixture) -> None:
        data = {"id": "wf-001", "name": "Test"}
        render.render_json(data)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed == data

    def test_paginated_list_includes_items_and_pagination(self, capsys: pytest.CaptureFixture) -> None:
        data = {
            "items": [{"id": "wf-001"}],
            "pagination": {"next_offset": 50, "has_next": False, "total": 1, "limit": 50},
        }
        render.render_json(data)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert "items" in parsed
        assert "pagination" in parsed


class TestRenderTable:
    def test_three_rows_with_expected_columns(self, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NO_COLOR", "1")
        data = [
            {"id": "wf-001", "name": "Alpha"},
            {"id": "wf-002", "name": "Beta"},
            {"id": "wf-003", "name": "Gamma"},
        ]
        render.render_table(data, columns=["id", "name"])
        captured = capsys.readouterr()
        assert "wf-001" in captured.out
        assert "Alpha" in captured.out
        assert "wf-003" in captured.out

    def test_empty_list_prints_no_results(self, capsys: pytest.CaptureFixture) -> None:
        render.render_table([], columns=["id", "name"])
        captured = capsys.readouterr()
        assert "No results" in captured.out

    def test_no_color_env_disables_rich(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NO_COLOR", "1")
        assert render._use_color() is False

    def test_no_color_flag_via_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NO_COLOR", "1")
        assert render._use_color() is False
