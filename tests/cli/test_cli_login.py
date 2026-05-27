"""Tests for `onepin login` command. Pending Fern SDK regen."""
from __future__ import annotations

import pytest
from typer.testing import CliRunner

from onepin._cli.main import app

runner = CliRunner()


class TestLogin:
    def test_stub_exits_1(self, tmp_home) -> None:
        """Until Fern regen, login exits 1 with not-implemented message."""
        result = runner.invoke(app, ["login", "--key", "op_live_test"])
        assert result.exit_code == 1
        assert "not implemented" in result.output.lower() or "not implemented" in (result.stderr or "").lower()

    def test_stub_without_key_exits_1(self, tmp_home) -> None:
        result = runner.invoke(app, ["login"], input="op_live_test\n")
        assert result.exit_code == 1
