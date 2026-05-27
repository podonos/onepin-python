"""Tests for `onepin whoami` command. Pending Fern SDK regen."""
from __future__ import annotations

import pytest
from typer.testing import CliRunner

from onepin._cli.main import app

runner = CliRunner()


class TestWhoami:
    def test_stub_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["whoami"])
        assert result.exit_code == 1

    def test_stub_with_api_key_flag_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["--api-key", "op_live_test", "whoami"])
        assert result.exit_code == 1
