"""The SKILL.md playback helpers are shipped code, not prose: parse them in every shell we document.

The PowerShell block cannot run on the maintainer's machine; the ``windows-latest`` CI leg is what
actually exercises ``test_windows_playback_helpers_parse``.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from onepin._cli.commands import skill


def _bundled(name: str) -> str:
    # Normalise first: a Windows checkout hands these back with CRLF, and an `\n` pattern then
    # matches nothing at all — which fails open, silently extracting zero snippets to check.
    return dict(skill._bundled_skill_files())[name].decode().replace("\r\n", "\n")


def _blocks(lang: str, name: str = "SKILL.md") -> list[str]:
    return re.findall(rf"```{lang}\n(.*?)```", _bundled(name), re.S)


def _posix_helpers() -> list[str]:
    return [b for b in _blocks("bash") if "play()" in b or "announce()" in b]


def test_skill_documents_playback_helpers() -> None:
    assert _posix_helpers(), "SKILL.md lost its play()/announce() helpers"
    assert _blocks("powershell"), "SKILL.md lost its Windows playback helpers"


@pytest.mark.parametrize("shell", ["bash", "zsh"])
def test_posix_playback_helpers_parse(shell: str, tmp_path: Path) -> None:
    if sys.platform == "win32":
        # `bash` on a Windows runner resolves to the WSL launcher stub, which exits 1 with no
        # distro installed — so it would fail the snippet rather than parse it. These blocks are
        # for POSIX shells anyway; the ubuntu and macos legs are what check them.
        pytest.skip("POSIX shells are checked on the non-Windows legs")
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


class TestBuildableGuidance:
    """The bundled skill is the agent's whole contract, so the gate has to be in it, not just in --help.

    An agent that never passes ``--buildable`` gets the ungated catalogue and no error, which is
    the same silent-wrong-list failure the gate exists to close -- only reached through the docs
    rather than through an old server.
    """

    def test_voice_selection_teaches_the_gate(self) -> None:
        text = _bundled("SKILL.md")

        assert "--buildable" in text
        # The rule that makes it usable at all: the flag is meaningless without a locale.
        assert "requires `--language`" in text or "It needs `--language`" in text

    def test_the_pinning_paths_carry_the_gate(self) -> None:
        """`voice_map` and `set-voice` write a voice into the saved workflow -- gate both."""
        text = _bundled("SKILL.md")
        pinning = [line for line in text.splitlines() if "voice_map" in line or "set-voice" in line]

        assert any("--buildable" in line for line in pinning), (
            "no voice_map / set-voice guidance mentions --buildable, so the agent can still pin a "
            "voice the API cannot synthesize"
        )

    def test_reference_recipe_uses_the_gate(self) -> None:
        recipes = [block for block in _blocks("bash", "reference.md") if "voices list" in block]

        assert recipes, "reference.md lost its voices list recipe"
        assert any("--buildable" in block for block in recipes)

    def test_the_gate_is_never_shown_on_a_command_that_rejects_it(self) -> None:
        """R5/facets: `show`, `similar` and `facets` do not take it -- an example that says they do
        would be copied verbatim into a usage error."""
        ungated = ("voices show", "voices similar", "voices facets")
        for name in ("SKILL.md", "reference.md"):
            for block in _blocks("bash", name):
                for line in block.splitlines():
                    if "--buildable" in line:
                        assert not any(command in line for command in ungated), (
                            f"{name} shows --buildable on a command that rejects it: {line.strip()!r}"
                        )

    def test_the_limits_of_the_gate_are_stated(self) -> None:
        """It is not a guarantee and not a durable fact; both are easy to overclaim from the name."""
        text = _bundled("SKILL.md")

        assert "not a guarantee" in text.lower()
        assert "Don't cache it" in text or "do not cache" in text.lower()
