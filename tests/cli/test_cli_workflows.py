"""Tests for `onepin workflows` commands. Pending Fern SDK regen."""
from __future__ import annotations

import pytest
from typer.testing import CliRunner

from onepin._cli.main import app

runner = CliRunner()


class TestWorkflowsStubs:
    def test_list_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["workflows", "list"])
        assert result.exit_code == 1

    def test_list_json_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["workflows", "list", "--json"])
        assert result.exit_code == 1

    def test_show_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["workflows", "show", "wf-00000000-0000-0000-0000-000000000001"])
        assert result.exit_code == 1

    def test_run_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["workflows", "run", "wf-00000000-0000-0000-0000-000000000001"])
        assert result.exit_code == 1

    def test_runs_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["workflows", "runs", "wf-00000000-0000-0000-0000-000000000001"])
        assert result.exit_code == 1
