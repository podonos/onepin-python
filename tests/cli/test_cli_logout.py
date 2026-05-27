"""Tests for `onepin logout` command. Pending Fern SDK regen."""
from __future__ import annotations

import pytest
from typer.testing import CliRunner

from onepin._cli.main import app

runner = CliRunner()


class TestLogout:
    def test_stub_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["logout"])
        assert result.exit_code == 1

    def test_stub_missing_file_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["logout"])
        assert result.exit_code == 1
