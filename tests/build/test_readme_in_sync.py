"""Drift gate: the README CLI command reference must match the live command tree.

The authoritative command inventory in README.md is generated from the assembled CLI command
tree (``onepin._cli._manifest.render_markdown`` -- the same source of truth as
``onepin schema``). This test extracts the committed block between the stable markers and
asserts it is byte-equal to a fresh render, so the README can never silently go stale: if the
CLI surface changes without regenerating, CI fails with an actionable message.

Refresh with: ``python scripts/gen_cli_docs.py``.
"""

from __future__ import annotations

from pathlib import Path

from onepin._cli._manifest import render_markdown

_BEGIN_MARKER = "<!-- BEGIN GENERATED: cli-commands -->"
_END_MARKER = "<!-- END GENERATED: cli-commands -->"
_README = Path(__file__).resolve().parents[2] / "README.md"
_STALE_MESSAGE = "README CLI reference is stale — run: python scripts/gen_cli_docs.py"


def _extract_block(text: str) -> str:
    """Return the README content strictly between the marker pair (markers excluded)."""
    begin = text.index(_BEGIN_MARKER) + len(_BEGIN_MARKER)
    end = text.index(_END_MARKER)
    return text[begin:end].strip("\n") + "\n"


def test_markers_present_exactly_once() -> None:
    text = _README.read_text(encoding="utf-8")
    assert text.count(_BEGIN_MARKER) == 1, f"expected exactly one {_BEGIN_MARKER!r}"
    assert text.count(_END_MARKER) == 1, f"expected exactly one {_END_MARKER!r}"


def test_readme_cli_reference_in_sync() -> None:
    text = _README.read_text(encoding="utf-8")
    committed = _extract_block(text)
    expected = render_markdown()
    assert committed == expected, _STALE_MESSAGE
