"""Tests for credential resolution priority chain."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from onepin._cli.auth.resolver import ResolvedCredentials, resolve_credentials


class TestResolveCredentials:
    def test_flag_wins_over_env_and_file(self, tmp_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ONEPIN_API_KEY", "op_live_env")
        result = resolve_credentials(flag_api_key="op_live_flag")
        assert result.api_key == "op_live_flag"
        assert result.source == "flag"

    def test_env_wins_over_file(self, tmp_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # Write a credentials file
        creds_dir = tmp_home / ".onepin"
        creds_dir.mkdir(mode=0o700)
        (creds_dir / "credentials").write_text('[default]\napi_key = "op_live_file"\nbase_url = "https://api.onepin.ai"\n')

        monkeypatch.setenv("ONEPIN_API_KEY", "op_live_env")
        result = resolve_credentials()
        assert result.api_key == "op_live_env"
        assert result.source == "env"

    def test_file_wins_when_no_flag_no_env(self, tmp_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ONEPIN_API_KEY", raising=False)
        creds_dir = tmp_home / ".onepin"
        creds_dir.mkdir(mode=0o700)
        (creds_dir / "credentials").write_text('[default]\napi_key = "op_live_file"\nbase_url = "https://api.onepin.ai"\n')

        result = resolve_credentials()
        assert result.api_key == "op_live_file"
        assert result.source == "file"

    def test_all_absent_returns_none(self, tmp_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ONEPIN_API_KEY", raising=False)
        result = resolve_credentials()
        assert result.api_key is None
        assert result.source == "default"

    def test_malformed_toml_raises_system_exit(self, tmp_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ONEPIN_API_KEY", raising=False)
        creds_dir = tmp_home / ".onepin"
        creds_dir.mkdir(mode=0o700)
        (creds_dir / "credentials").write_text("this is not [ valid toml !!!")

        with pytest.raises(SystemExit):
            resolve_credentials()

    def test_file_multiple_profiles_uses_default(self, tmp_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ONEPIN_API_KEY", raising=False)
        creds_dir = tmp_home / ".onepin"
        creds_dir.mkdir(mode=0o700)
        content = '[default]\napi_key = "op_live_default"\nbase_url = "https://api.onepin.ai"\n[staging]\napi_key = "op_live_staging"\nbase_url = "https://staging-api.onepin.ai"\n'
        (creds_dir / "credentials").write_text(content)

        result = resolve_credentials()
        assert result.api_key == "op_live_default"
        assert result.source == "file"

    def test_source_flag_reported_correctly(self, tmp_home: Path) -> None:
        result = resolve_credentials(flag_api_key="op_live_x")
        assert result.source == "flag"

    def test_source_env_reported_correctly(self, tmp_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ONEPIN_API_KEY", "op_live_env")
        result = resolve_credentials()
        assert result.source == "env"

    def test_source_file_reported_correctly(self, tmp_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ONEPIN_API_KEY", raising=False)
        creds_dir = tmp_home / ".onepin"
        creds_dir.mkdir(mode=0o700)
        (creds_dir / "credentials").write_text('[default]\napi_key = "op_live_file"\nbase_url = "https://api.onepin.ai"\n')
        result = resolve_credentials()
        assert result.source == "file"
