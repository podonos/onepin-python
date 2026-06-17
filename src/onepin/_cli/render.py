"""Rich table + JSON output adapter.

Honors NO_COLOR env var (W3C spec) and non-TTY detection.
Errors always go to stderr; --json stdout is clean data only.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Optional


def _use_color() -> bool:
    """Return True if ANSI color should be used.

    Honors the ``--no-color`` flag (captured in root state), then the W3C
    ``NO_COLOR`` env var, then TTY detection.
    """
    from onepin._cli import _state

    if _state.root_options.get("no_color"):
        return False
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


def render_json(data: Any) -> None:
    """Emit JSON to stdout. No envelope -- just the raw payload (.data)."""
    print(json.dumps(data, indent=2, default=str))


def render_table(
    data: List[Dict[str, Any]],
    columns: List[str],
    title: Optional[str] = None,
) -> None:
    """Render a list of dicts as a rich table, or plain text if color is disabled.

    Args:
        data: List of row dicts. Keys must include all values in ``columns``.
        columns: Ordered list of column names to display.
        title: Optional table title shown above the table.
    """
    if not data:
        _print_no_results()
        return

    if _use_color():
        _render_rich_table(data, columns, title)
    else:
        _render_plain_table(data, columns, title)


def _print_no_results() -> None:
    print("No results.")


def _render_rich_table(data: List[Dict[str, Any]], columns: List[str], title: Optional[str]) -> None:
    try:
        from rich.console import Console
        from rich.table import Table
    except ImportError:  # pragma: no cover
        _render_plain_table(data, columns, title)
        return

    console = Console()
    table = Table(title=title, show_header=True, header_style="bold")
    for col in columns:
        table.add_column(col)
    for row in data:
        table.add_row(*[str(row.get(col, "")) for col in columns])
    console.print(table)


def _render_plain_table(data: List[Dict[str, Any]], columns: List[str], title: Optional[str]) -> None:
    if title:
        print(title)
    print("\t".join(columns))
    for row in data:
        print("\t".join(str(row.get(col, "")) for col in columns))
