"""Voice commands. Implementation pending first Fern SDK regen."""
from __future__ import annotations

import sys
from typing import Optional

import typer

app = typer.Typer(help="Browse available voices.", no_args_is_help=True)


@app.command(name="list")
def list_voices(
    limit: int = typer.Option(50, "--limit"),
    locale: Optional[str] = typer.Option(None, "--locale", help="Filter by locale (e.g. en-US)."),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """List available voices."""
    typer.echo("voices list: not implemented yet -- Fern SDK regen pending", err=True)
    sys.exit(1)
