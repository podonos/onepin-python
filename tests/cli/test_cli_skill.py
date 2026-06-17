"""Tests for the ``onepin skill install / path / uninstall`` command group.

These are pure-filesystem commands (no SDK, no auth, no network), so the tests just drive a
``tmp_home`` and assert the bundled skill folder lands in the right per-tool directories.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from onepin._cli._ctx import CliError
from onepin._cli.commands import skill
from onepin._cli.main import app

runner = CliRunner()


# === install =============================================================================


def test_install_personal_writes_real_skill(tmp_home: Path) -> None:
    result = runner.invoke(app, ["skill", "install", "--tool", "claude"])
    assert result.exit_code == 0, result.output

    skill = tmp_home / ".claude" / "skills" / "onepin" / "SKILL.md"
    reference = tmp_home / ".claude" / "skills" / "onepin" / "reference.md"
    assert skill.exists() and reference.exists()
    # Proves the real bundled file was copied (not a stub) — it teaches schema discovery.
    assert "onepin schema" in skill.read_text()


def test_install_does_not_require_auth(tmp_home: Path) -> None:
    # No --api-key, no credentials file: install is a local file op and must still succeed.
    result = runner.invoke(app, ["skill", "install", "--tool", "claude"])
    assert result.exit_code == 0, result.output
    assert (tmp_home / ".claude" / "skills" / "onepin" / "SKILL.md").exists()


def test_install_project_mode(tmp_home: Path, tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    monkeypatch.chdir(project)
    result = runner.invoke(app, ["skill", "install", "--project", "--tool", "cursor"])
    assert result.exit_code == 0, result.output
    # Cursor's project path is the shared .agents/skills.
    assert (project / ".agents" / "skills" / "onepin" / "SKILL.md").exists()
    # HOME must be untouched in project mode.
    assert not (tmp_home / ".cursor").exists()


def test_install_project_dedupes_shared_agents_dir(tmp_home: Path, tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    monkeypatch.chdir(project)
    result = runner.invoke(app, ["skill", "install", "--project", "--tool", "cursor", "--tool", "codex", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    # cursor + codex share one .agents/skills dir → a single deduped target listing both.
    assert len(payload["targets"]) == 1
    assert set(payload["targets"][0]["tools"]) == {"cursor", "codex"}


def test_install_all_tools(tmp_home: Path) -> None:
    result = runner.invoke(app, ["skill", "install", "--all"])
    assert result.exit_code == 0, result.output
    for sub in (".claude", ".cursor", ".codex", ".copilot", ".gemini"):
        assert (tmp_home / sub / "skills" / "onepin" / "SKILL.md").exists()


def test_install_autodetect_defaults_to_claude(tmp_home: Path) -> None:
    # Fresh HOME with no tool config dirs → falls back to Claude so bare /onepin works.
    result = runner.invoke(app, ["skill", "install"])
    assert result.exit_code == 0, result.output
    assert (tmp_home / ".claude" / "skills" / "onepin" / "SKILL.md").exists()


def test_install_autodetect_picks_existing_tool(tmp_home: Path) -> None:
    (tmp_home / ".cursor").mkdir()
    result = runner.invoke(app, ["skill", "install", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    tools = {t for target in payload["targets"] for t in target["tools"]}
    assert "cursor" in tools
    assert (tmp_home / ".cursor" / "skills" / "onepin" / "SKILL.md").exists()


def test_install_refuses_clobber_without_force(tmp_home: Path) -> None:
    skill = tmp_home / ".claude" / "skills" / "onepin" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("OLD")
    result = runner.invoke(app, ["skill", "install", "--tool", "claude"])
    assert result.exit_code == 1
    assert "FILE_EXISTS" in result.output
    assert skill.read_text() == "OLD"


def test_install_force_overwrites(tmp_home: Path) -> None:
    skill = tmp_home / ".claude" / "skills" / "onepin" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("OLD")
    result = runner.invoke(app, ["skill", "install", "--tool", "claude", "--force"])
    assert result.exit_code == 0, result.output
    assert skill.read_text() != "OLD"
    assert "onepin schema" in skill.read_text()


def test_install_json_output(tmp_home: Path) -> None:
    result = runner.invoke(app, ["skill", "install", "--tool", "claude", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["command"] == "/onepin"
    # Platform-neutral: str(Path) uses backslashes on Windows CI, so compare to a real Path.
    assert payload["targets"][0]["path"] == str(tmp_home / ".claude" / "skills" / "onepin")


def test_install_dir_creation_failure_maps_to_write_failed(tmp_home: Path) -> None:
    # A file where the skills dir should go → mkdir raises OSError → must map to WRITE_FAILED
    # (not an unhandled traceback that breaks the --json error envelope).
    skills = tmp_home / ".claude" / "skills"
    skills.parent.mkdir(parents=True)
    skills.write_text("not a directory")
    result = runner.invoke(app, ["skill", "install", "--tool", "claude", "--json"])
    assert result.exit_code == 1
    assert "WRITE_FAILED" in result.output


# === path ================================================================================


def test_path_reports_without_writing(tmp_home: Path) -> None:
    result = runner.invoke(app, ["skill", "path", "--tool", "claude", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["targets"][0]["exists"] is False
    # path must not create anything.
    assert not (tmp_home / ".claude").exists()


def test_path_reflects_install(tmp_home: Path) -> None:
    runner.invoke(app, ["skill", "install", "--tool", "claude"])
    result = runner.invoke(app, ["skill", "path", "--tool", "claude", "--json"])
    payload = json.loads(result.output)
    assert payload["targets"][0]["exists"] is True


# === uninstall ===========================================================================


def test_uninstall_yes_removes_only_leaf(tmp_home: Path) -> None:
    runner.invoke(app, ["skill", "install", "--tool", "claude"])
    leaf = tmp_home / ".claude" / "skills" / "onepin"
    assert leaf.exists()
    result = runner.invoke(app, ["skill", "uninstall", "--tool", "claude", "--yes"])
    assert result.exit_code == 0, result.output
    assert not leaf.exists()
    # The parent skills/ dir is preserved — we only delete our own onepin/ leaf.
    assert leaf.parent.exists()


def test_uninstall_confirm_prompt_removes(tmp_home: Path) -> None:
    runner.invoke(app, ["skill", "install", "--tool", "claude"])
    leaf = tmp_home / ".claude" / "skills" / "onepin"
    result = runner.invoke(app, ["skill", "uninstall", "--tool", "claude"], input="y\n")
    assert result.exit_code == 0, result.output
    assert not leaf.exists()


def test_uninstall_json_requires_yes(tmp_home: Path) -> None:
    runner.invoke(app, ["skill", "install", "--tool", "claude"])
    leaf = tmp_home / ".claude" / "skills" / "onepin"
    result = runner.invoke(app, ["skill", "uninstall", "--tool", "claude", "--json"])
    assert result.exit_code == 1
    assert "CONFIRMATION_REQUIRED" in result.output
    assert leaf.exists()  # nothing removed


def test_uninstall_idempotent_when_absent(tmp_home: Path) -> None:
    result = runner.invoke(app, ["skill", "uninstall", "--tool", "claude", "--yes", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["removed"] == []


def test_path_human_output(tmp_home: Path) -> None:
    result = runner.invoke(app, ["skill", "path", "--tool", "claude"])
    assert result.exit_code == 0, result.output
    assert str(tmp_home / ".claude" / "skills" / "onepin") in result.output
    assert "not installed" in result.output


def test_path_maps_clierror_from_resolution(tmp_home: Path, monkeypatch) -> None:
    def boom(tools, project):
        raise CliError("BOOM", "resolution failed")

    monkeypatch.setattr(skill, "_target_dirs", boom)
    result = runner.invoke(app, ["skill", "path", "--tool", "claude", "--json"])
    assert result.exit_code == 1
    assert "BOOM" in result.output


def test_uninstall_nothing_to_remove_human(tmp_home: Path) -> None:
    result = runner.invoke(app, ["skill", "uninstall", "--tool", "claude", "--yes"])
    assert result.exit_code == 0, result.output
    assert "Nothing to remove" in result.output
