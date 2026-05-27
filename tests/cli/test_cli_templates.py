"""Tests for `onepin templates` commands. Pending Fern SDK regen."""

from __future__ import annotations

from typer.testing import CliRunner

from onepin._cli.main import app

runner = CliRunner()


class TestTemplatesStubs:
    def test_list_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["templates", "list"])
        assert result.exit_code == 1

    def test_list_json_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["templates", "list", "--json"])
        assert result.exit_code == 1

    def test_show_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["templates", "show", "tmpl-00000000-0000-0000-0000-000000000001"])
        assert result.exit_code == 1

    def test_run_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["templates", "run", "tmpl-00000000-0000-0000-0000-000000000001"])
        assert result.exit_code == 1

    def test_run_with_name_exits_1(self, tmp_home) -> None:
        result = runner.invoke(
            app, ["templates", "run", "tmpl-00000000-0000-0000-0000-000000000001", "--name", "My Workflow"]
        )
        assert result.exit_code == 1
