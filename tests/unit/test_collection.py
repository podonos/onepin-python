"""Guard: the default pytest invocation must actually collect ``tests/build/``.

Everything in ``tests/build/`` is a gate on the Fern regen pipeline — the ``.fernignore``
guard, the README sync, the CLI<->SDK contract. All of it was dead for months: pytest's
default ``norecursedirs`` carries the bare pattern ``build``, which matches by basename, so
recursing from ``testpaths = ["tests"]`` skipped the directory whole. ``pytest -q`` reported a
green suite that had never imported those files, and guards that were red the day they were
written merged to main on green CI.

``pyproject.toml`` drops ``build`` from ``norecursedirs`` and ignores the artifact tree by path
instead. That is one word in a config file, so this asserts the *behaviour* from outside: run
collection the way CI runs it and look for a test that lives in there.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parents[2]

# Not a module this file imports: the point is what a *separate* pytest process, configured
# only by pyproject.toml, decides to collect.
_CANARIES = (
    "tests/build/test_sdk_contract.py",
    "tests/build/test_cli_preserved.py",
)


def test_default_collection_includes_tests_build() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        capture_output=True,
        text=True,
        cwd=_REPO_ROOT,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    missing = [canary for canary in _CANARIES if canary not in result.stdout]
    assert not missing, (
        f"`pytest --collect-only` does not reach {missing} — tests/build/ is being skipped "
        f"again, so none of its regen guards gate anything. Check `norecursedirs` in "
        f"pyproject.toml (pytest's default value contains `build`)."
    )
