# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""Auto-format Python edits in the hand-rolled subpackages.

Runs after Claude Code's Edit/Write/MultiEdit tools. Scoped to
`src/onepin/_cli/` and `tests/` — the Fern-generated tree under
`src/onepin/` (excluding `_cli/`) is intentionally skipped because
those files are overwritten on every regen.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ALLOWED_PREFIXES = ("src/onepin/_cli/", "tests/")
PROJECT_DIR = Path(__file__).resolve().parents[2]


def in_scope(rel: str) -> bool:
    return rel.startswith(ALLOWED_PREFIXES)


def run() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return

    if payload.get("tool_name") not in ("Write", "Edit", "MultiEdit"):
        return

    file_path = payload.get("tool_input", {}).get("file_path")
    if not file_path:
        return

    path = Path(file_path)
    if path.suffix not in (".py", ".pyi"):
        return

    try:
        rel = path.resolve().relative_to(PROJECT_DIR).as_posix()
    except ValueError:
        return

    if not in_scope(rel):
        return

    # `check --fix` first so import / lint fixes settle before formatter
    # canonicalizes the result (per ruff usage guidance).
    for cmd in (
        ["uv", "run", "ruff", "check", "--fix", str(path)],
        ["uv", "run", "ruff", "format", str(path)],
    ):
        try:
            result = subprocess.run(
                cmd,
                cwd=PROJECT_DIR,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError):
            return
        if result.returncode != 0:
            sys.stderr.write(f"[post-edit-format] {cmd[3]} exited {result.returncode}\n")


def main() -> None:
    try:
        run()
    except Exception:
        # Best-effort hook: never block Claude on formatter errors.
        return


if __name__ == "__main__":
    main()
