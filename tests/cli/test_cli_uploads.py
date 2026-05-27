"""Tests for `onepin uploads` commands. Pending Fern SDK regen."""

from __future__ import annotations

from typer.testing import CliRunner

from onepin._cli.main import app

runner = CliRunner()


class TestUploadsStubs:
    def test_create_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["uploads", "create", "--file", "script.txt", "--category", "script"])
        assert result.exit_code == 1

    def test_create_json_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["uploads", "create", "--file", "script.txt", "--category", "script", "--json"])
        assert result.exit_code == 1

    def test_confirm_exits_1(self, tmp_home) -> None:
        result = runner.invoke(
            app,
            [
                "uploads",
                "confirm",
                "upl-00000000-0000-0000-0000-000000000001",
                "--workflow-id",
                "wf-00000000-0000-0000-0000-000000000001",
            ],
        )
        assert result.exit_code == 1

    def test_delete_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["uploads", "delete", "upl-00000000-0000-0000-0000-000000000001"])
        assert result.exit_code == 1
