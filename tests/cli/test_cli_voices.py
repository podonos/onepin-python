"""Tests for `onepin voices` commands. Pending Fern SDK regen."""

from __future__ import annotations

from typer.testing import CliRunner

from onepin._cli.main import app

runner = CliRunner()


class TestVoicesStubs:
    def test_list_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["voices", "list"])
        assert result.exit_code == 1

    def test_list_json_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["voices", "list", "--json"])
        assert result.exit_code == 1

    def test_list_locale_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["voices", "list", "--locale", "en-US"])
        assert result.exit_code == 1
