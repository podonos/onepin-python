"""Tests for credentials file read/write."""
from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import pytest

from onepin._cli.auth.credentials import delete_credentials, read_credentials, write_credentials


class TestWriteCredentials:
    def test_creates_parent_dir_with_0700(self, tmp_home: Path) -> None:
        write_credentials("op_live_test", "https://api.onepin.ai")
        parent = tmp_home / ".onepin"
        assert parent.exists()
        if os.name != "nt":
            mode = oct(stat.S_IMODE(parent.stat().st_mode))
            assert mode == oct(0o700)

    def test_writes_file_with_0600(self, tmp_home: Path) -> None:
        path = write_credentials("op_live_test", "https://api.onepin.ai")
        assert path.exists()
        if os.name != "nt":
            mode = oct(stat.S_IMODE(path.stat().st_mode))
            assert mode == oct(0o600)

    def test_overwrites_existing_preserving_mode(self, tmp_home: Path) -> None:
        write_credentials("op_live_first", "https://api.onepin.ai")
        path = write_credentials("op_live_second", "https://api.onepin.ai")
        data = read_credentials()
        assert data is not None
        assert data["default"]["api_key"] == "op_live_second"
        if os.name != "nt":
            mode = oct(stat.S_IMODE(path.stat().st_mode))
            assert mode == oct(0o600)

    def test_windows_still_writes_file(self, tmp_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """On Windows os.chmod is a no-op; file still written successfully."""
        monkeypatch.setattr(os, "name", "nt")
        path = write_credentials("op_live_test", "https://api.onepin.ai")
        assert path.exists()

    def test_roundtrip(self, tmp_home: Path) -> None:
        write_credentials("op_live_roundtrip", "https://api.onepin.ai")
        data = read_credentials()
        assert data is not None
        assert data["default"]["api_key"] == "op_live_roundtrip"
        assert data["default"]["base_url"] == "https://api.onepin.ai"


class TestReadCredentials:
    def test_returns_none_if_missing(self, tmp_home: Path) -> None:
        result = read_credentials()
        assert result is None

    def test_returns_data_if_exists(self, tmp_home: Path) -> None:
        write_credentials("op_live_x", "https://api.onepin.ai")
        data = read_credentials()
        assert data is not None
        assert "default" in data

    def test_malformed_toml_raises_system_exit(self, tmp_home: Path) -> None:
        creds_dir = tmp_home / ".onepin"
        creds_dir.mkdir(mode=0o700, exist_ok=True)
        (creds_dir / "credentials").write_text("not [ valid toml !!!")
        with pytest.raises(SystemExit):
            read_credentials()


class TestDeleteCredentials:
    def test_deletes_existing_file(self, tmp_home: Path) -> None:
        write_credentials("op_live_x", "https://api.onepin.ai")
        result = delete_credentials()
        assert result is True
        assert read_credentials() is None

    def test_no_op_if_missing(self, tmp_home: Path) -> None:
        result = delete_credentials()
        assert result is False
