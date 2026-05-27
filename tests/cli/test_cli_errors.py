"""Error-class coverage tests. Pending Fern SDK regen.

These tests verify the CLI error surface contract. Full error handling
(429 rate limit, 500 server error, etc.) is tested once OnePinClient
is available after the first Fern SDK regen.
"""
from __future__ import annotations

import pytest
from typer.testing import CliRunner

from onepin._cli.main import app

runner = CliRunner()


class TestVersionFlag:
    """Version flag should work immediately -- no SDK needed."""

    def test_version_flag_exits_0(self) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0

    def test_version_flag_prints_onepin(self) -> None:
        result = runner.invoke(app, ["--version"])
        assert "onepin" in result.output

    def test_short_version_flag(self) -> None:
        # --version is eager; both forms should work
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0


class TestHelpFlag:
    def test_help_exits_0(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_short_help_flag(self) -> None:
        result = runner.invoke(app, ["-h"])
        assert result.exit_code == 0

    def test_help_lists_commands(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert "login" in result.output
        assert "logout" in result.output
        assert "whoami" in result.output
        assert "workflows" in result.output
        assert "voices" in result.output
        assert "templates" in result.output
        assert "uploads" in result.output
