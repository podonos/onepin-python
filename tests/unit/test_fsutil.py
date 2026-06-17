"""Unit tests for the shared atomic-write helper, focused on its cleanup/error branches."""

from __future__ import annotations

from pathlib import Path

import pytest

from onepin._cli import _fsutil


def test_atomic_write_happy(tmp_path: Path) -> None:
    dest = tmp_path / "f.txt"
    _fsutil.atomic_write_bytes(dest, b"hello", force=False)
    assert dest.read_bytes() == b"hello"


def test_atomic_write_refuses_existing_without_force(tmp_path: Path) -> None:
    dest = tmp_path / "f.txt"
    dest.write_bytes(b"old")
    with pytest.raises(FileExistsError):
        _fsutil.atomic_write_bytes(dest, b"new", force=False)
    assert dest.read_bytes() == b"old"


def test_atomic_write_force_overwrites(tmp_path: Path) -> None:
    dest = tmp_path / "f.txt"
    dest.write_bytes(b"old")
    _fsutil.atomic_write_bytes(dest, b"new", force=True)
    assert dest.read_bytes() == b"new"


def test_atomic_write_cleans_reservation_on_mkstemp_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dest = tmp_path / "f.txt"

    def boom(*args: object, **kwargs: object) -> object:
        raise OSError("no temp")

    monkeypatch.setattr(_fsutil.tempfile, "mkstemp", boom)
    with pytest.raises(OSError):
        _fsutil.atomic_write_bytes(dest, b"x", force=False)
    # The O_EXCL reservation placeholder must be cleaned up so a retry isn't blocked.
    assert not dest.exists()


def test_atomic_write_cleans_up_on_write_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dest = tmp_path / "f.txt"

    def boom(*args: object, **kwargs: object) -> object:
        raise OSError("disk full")

    monkeypatch.setattr(_fsutil.os, "replace", boom)
    with pytest.raises(OSError):
        _fsutil.atomic_write_bytes(dest, b"x", force=False)
    # Both the temp file and the reservation are removed — no partial or leftover files.
    assert not dest.exists()
    assert list(tmp_path.iterdir()) == []


def test_try_unlink_missing_path_is_silent(tmp_path: Path) -> None:
    _fsutil.try_unlink(tmp_path / "does-not-exist")  # must not raise
