"""Regen-sync guard: assert the hand-rolled CLI + PEP 561 markers survive a Fern regen.

The upstream ``publish-sdks.yml`` rsync (in ``onepin-sdks``) preserves
``src/onepin/_cli/`` and the ``py.typed`` markers when it syncs generated code into
this repo. That guard lives in another repo, so this test fails loudly in CI here if a
regen ever clobbers the hand-rolled CLI or drops the typing markers.
"""

from __future__ import annotations

import importlib
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src" / "onepin"


def test_cli_package_present() -> None:
    cli = _SRC / "_cli"
    assert cli.is_dir(), "src/onepin/_cli/ missing — a Fern regen may have clobbered the hand-rolled CLI"
    assert (cli / "main.py").is_file(), "src/onepin/_cli/main.py missing"
    assert (cli / "__init__.py").is_file(), "src/onepin/_cli/__init__.py missing"


def test_py_typed_markers_present() -> None:
    assert (_SRC / "py.typed").is_file(), "src/onepin/py.typed missing — run scripts/post_fern.sh"
    assert (_SRC / "_cli" / "py.typed").is_file(), "src/onepin/_cli/py.typed missing — run scripts/post_fern.sh"


def test_cli_app_importable() -> None:
    module = importlib.import_module("onepin._cli.main")
    assert hasattr(module, "app"), "onepin._cli.main:app missing — CLI entry point broken"
