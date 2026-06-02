#!/usr/bin/env python
"""Refresh the generated CLI command reference in README.md.

Thin entrypoint: it imports the in-package renderer (``onepin._cli._manifest.render_markdown``
-- the single source of truth, built from the assembled command tree) and splices its output
into README.md between the stable markers::

    <!-- BEGIN GENERATED: cli-commands -->
    ... generated block ...
    <!-- END GENERATED: cli-commands -->

Humans run ``python scripts/gen_cli_docs.py`` after changing the CLI surface.
CI never runs this; ``tests/build/test_readme_in_sync.py`` fails instead if the committed
block drifts from the renderer, pointing back to this command.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a plain script (``python scripts/gen_cli_docs.py``) without an install.
_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from onepin._cli._manifest import render_markdown  # noqa: E402

BEGIN_MARKER = "<!-- BEGIN GENERATED: cli-commands -->"
END_MARKER = "<!-- END GENERATED: cli-commands -->"

README = Path(__file__).resolve().parent.parent / "README.md"


def splice(readme_text: str, generated: str) -> str:
    """Return ``readme_text`` with the region between the markers replaced by ``generated``.

    Raises:
        SystemExit: if either marker is missing or out of order (the README must already
            contain the marker pair; this script only refreshes the content between them).
    """
    begin = readme_text.find(BEGIN_MARKER)
    end = readme_text.find(END_MARKER)
    if begin == -1 or end == -1 or end < begin:
        raise SystemExit(
            f"README.md is missing the marker pair {BEGIN_MARKER!r} / {END_MARKER!r}; "
            "add them around the generated CLI command reference first."
        )
    head = readme_text[: begin + len(BEGIN_MARKER)]
    tail = readme_text[end:]
    return f"{head}\n{generated.rstrip(chr(10))}\n{tail}"


def main() -> None:
    text = README.read_text(encoding="utf-8")
    updated = splice(text, render_markdown())
    if updated != text:
        README.write_text(updated, encoding="utf-8")
        print(f"Updated {README}")
    else:
        print(f"{README} already up to date")


if __name__ == "__main__":
    main()
