"""Unit tests for ``onepin skill`` helpers: tool selection, target-dir resolution, bundled payload."""

from __future__ import annotations

from pathlib import Path

import pytest

from onepin._cli._ctx import CliError
from onepin._cli.commands import skill


def test_bundled_skill_files_present_and_nonempty() -> None:
    files = dict(skill._bundled_skill_files())
    assert "SKILL.md" in files
    assert "reference.md" in files
    assert b"onepin schema" in files["SKILL.md"]


def test_select_tools_explicit_dedupes_and_preserves_order() -> None:
    tools = skill._select_tools([skill._Tool.cursor, skill._Tool.claude, skill._Tool.cursor], all_tools=False)
    assert tools == ["cursor", "claude"]


def test_select_tools_all() -> None:
    assert set(skill._select_tools(None, all_tools=True)) == {"claude", "cursor", "codex", "copilot", "gemini"}


def test_select_tools_autodetect_defaults_to_claude(tmp_home: Path) -> None:
    assert skill._select_tools(None, all_tools=False) == ["claude"]


def test_select_tools_autodetect_finds_existing(tmp_home: Path) -> None:
    (tmp_home / ".gemini").mkdir()
    assert "gemini" in skill._select_tools(None, all_tools=False)


def test_target_dirs_home_is_per_tool(tmp_home: Path) -> None:
    dirs = [d for _, d in skill._target_dirs(["claude", "cursor"], project=False)]
    assert tmp_home / ".claude" / "skills" / "onepin" in dirs
    assert tmp_home / ".cursor" / "skills" / "onepin" in dirs


def test_target_dirs_project_dedupes_shared_agents(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    targets = skill._target_dirs(["cursor", "codex", "copilot", "gemini"], project=True)
    assert len(targets) == 1
    labels, directory = targets[0]
    assert set(labels) == {"cursor", "codex", "copilot", "gemini"}
    assert directory == tmp_path / ".agents" / "skills" / "onepin"


def test_remove_skill_dir_refuses_non_leaf(tmp_path: Path) -> None:
    # The rmtree safety guard: only a dir literally named "onepin" may be removed.
    guarded = tmp_path / "skills"
    guarded.mkdir()
    (guarded / "keep.txt").write_text("x")
    with pytest.raises(CliError) as exc:
        skill._remove_skill_dir(guarded)
    assert exc.value.code == "WRITE_FAILED"
    assert guarded.exists()  # never removed


def test_bundled_skill_files_missing_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(skill, "_SKILL_NAME", "does-not-exist")
    with pytest.raises(CliError) as exc:
        skill._bundled_skill_files()
    assert exc.value.code == "SKILL_PAYLOAD_MISSING"


def test_bundled_skill_files_empty_payload_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dir resolves but yields nothing shippable (all .py / non-files) -> SKILL_PAYLOAD_MISSING."""
    import importlib.resources

    class _Entry:
        def __init__(self, name: str, is_file: bool) -> None:
            self.name = name
            self._is_file = is_file

        def is_file(self) -> bool:
            return self._is_file

    class _Root:
        def joinpath(self, *_parts: str) -> _Root:
            return self

        def iterdir(self) -> list[_Entry]:
            return [_Entry("helper.py", is_file=True), _Entry("nested", is_file=False)]

    monkeypatch.setattr(importlib.resources, "files", lambda _pkg: _Root())
    with pytest.raises(CliError) as exc:
        skill._bundled_skill_files()
    assert exc.value.code == "SKILL_PAYLOAD_MISSING"


def test_write_maps_oserror_to_write_failed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(dest: Path, content: bytes, *, force: bool) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(skill._fsutil, "atomic_write_bytes", boom)
    with pytest.raises(CliError) as exc:
        skill._write(tmp_path / "SKILL.md", b"x", force=True)
    assert exc.value.code == "WRITE_FAILED"


def test_remove_skill_dir_rmtree_oserror_maps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    leaf = tmp_path / "onepin"
    leaf.mkdir()

    def boom(path: object) -> None:
        raise OSError("directory busy")

    monkeypatch.setattr(skill.shutil, "rmtree", boom)
    with pytest.raises(CliError) as exc:
        skill._remove_skill_dir(leaf)
    assert exc.value.code == "WRITE_FAILED"
