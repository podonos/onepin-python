"""Tests for `onepin logout` command."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from onepin._cli.main import app

runner = CliRunner()


class TestLogout:
    def test_file_exists_deleted_and_prints_success(self, tmp_home: Path) -> None:
        """Credentials file exists: deleted, prints success line."""
        creds_dir = tmp_home / ".onepin"
        creds_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        creds_path = creds_dir / "credentials"
        creds_path.write_text('[default]\napi_key = "op_live_x"\nbase_url = "https://api.onepin.ai"\n')

        result = runner.invoke(app, ["logout"])

        assert result.exit_code == 0, result.output
        assert "Removed credentials" in result.output
        assert not creds_path.exists()

    def test_file_missing_idempotent_prints_success(self, tmp_home: Path) -> None:
        """No credentials file: still exits 0 and prints success (idempotent)."""
        result = runner.invoke(app, ["logout"])

        assert result.exit_code == 0, result.output
        assert "Removed credentials" in result.output
