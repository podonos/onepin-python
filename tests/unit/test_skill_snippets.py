"""The SKILL.md playback helpers are shipped code, not prose: parse them in every shell we document.

The PowerShell block cannot run on the maintainer's machine; the ``windows-latest`` CI leg is what
actually exercises ``test_windows_playback_helpers_parse``.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from onepin._cli.commands import skill


def _blocks(lang: str) -> list[str]:
    # Normalise first: a Windows checkout hands these back with CRLF, and an `\n` pattern then
    # matches nothing at all — which fails open, silently extracting zero snippets to check.
    text = dict(skill._bundled_skill_files())["SKILL.md"].decode().replace("\r\n", "\n")
    return re.findall(rf"```{lang}\n(.*?)```", text, re.S)


def _posix_helpers() -> list[str]:
    return [b for b in _blocks("bash") if "play()" in b or "announce()" in b]


def test_skill_documents_playback_helpers() -> None:
    assert _posix_helpers(), "SKILL.md lost its play()/announce() helpers"
    assert _blocks("powershell"), "SKILL.md lost its Windows playback helpers"


@pytest.mark.parametrize("shell", ["bash", "zsh"])
def test_posix_playback_helpers_parse(shell: str, tmp_path: Path) -> None:
    if shutil.which(shell) is None:
        pytest.skip(f"{shell} not installed")
    for index, block in enumerate(_posix_helpers()):
        src = tmp_path / f"{shell}-{index}.sh"
        src.write_text(block, encoding="utf-8", newline="\n")
        proc = subprocess.run([shell, "-n", str(src)], capture_output=True, text=True)
        assert proc.returncode == 0, f"{shell} -n rejected SKILL.md block {index}:\n{proc.stderr}"


def test_windows_playback_helpers_parse(tmp_path: Path) -> None:
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if powershell is None:
        pytest.skip("no PowerShell on this machine (the windows-latest CI leg covers it)")
    for index, block in enumerate(_blocks("powershell")):
        src = tmp_path / f"block-{index}.ps1"
        src.write_text(block, encoding="utf-8", newline="\n")
        check = (
            "$errors = $null; "
            "[System.Management.Automation.Language.Parser]::ParseFile("
            f"'{src}', [ref]$null, [ref]$errors) > $null; "
            "if ($errors.Count) { $errors | ForEach-Object { $_.Message }; exit 1 }"
        )
        proc = subprocess.run([powershell, "-NoProfile", "-Command", check], capture_output=True, text=True)
        assert proc.returncode == 0, f"PowerShell rejected SKILL.md block {index}:\n{proc.stdout}{proc.stderr}"
