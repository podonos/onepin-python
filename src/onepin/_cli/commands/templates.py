"""Template commands. Implementation pending first Fern SDK regen."""

from __future__ import annotations

import sys
from typing import Optional

import typer

app = typer.Typer(help="Browse and run gallery templates.", no_args_is_help=True)


@app.command(name="list")
def list_templates(
    limit: int = typer.Option(50, "--limit"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """List gallery templates."""
    typer.echo("templates list: not implemented yet -- Fern SDK regen pending", err=True)
    sys.exit(1)


@app.command(name="show")
def show_template(
    template_id: str = typer.Argument(..., help="Template UUID."),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Show details of a single template."""
    typer.echo("templates show: not implemented yet -- Fern SDK regen pending", err=True)
    sys.exit(1)


@app.command(name="run")
def run_template(
    template_id: str = typer.Argument(..., help="Template UUID."),
    name: Optional[str] = typer.Option(None, "--name", help="Name for the cloned workflow."),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Clone a template into a workflow and start a run (convenience two-call).

    Prints both the new workflow ID and the new run ID.
    """
    typer.echo("templates run: not implemented yet -- Fern SDK regen pending", err=True)
    sys.exit(1)
