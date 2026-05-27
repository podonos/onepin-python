"""Workflow commands. Implementation pending first Fern SDK regen."""

from __future__ import annotations

import sys
from typing import Optional

import typer

app = typer.Typer(help="Manage workflows.", no_args_is_help=True)


@app.command(name="list")
def list_workflows(
    limit: int = typer.Option(50, "--limit"),
    sort: Optional[str] = typer.Option(None, "--sort"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """List workflows in the current workspace."""
    typer.echo("workflows list: not implemented yet -- Fern SDK regen pending", err=True)
    sys.exit(1)


@app.command(name="show")
def show_workflow(
    workflow_id: str = typer.Argument(..., help="Workflow UUID."),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Show details of a single workflow."""
    typer.echo("workflows show: not implemented yet -- Fern SDK regen pending", err=True)
    sys.exit(1)


@app.command(name="run")
def run_workflow(
    workflow_id: str = typer.Argument(..., help="Workflow UUID."),
    watch: bool = typer.Option(False, "--watch", help="Poll run status until terminal state."),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Start a workflow run."""
    typer.echo("workflows run: not implemented yet -- Fern SDK regen pending", err=True)
    sys.exit(1)


@app.command(name="runs")
def list_runs(
    workflow_id: str = typer.Argument(..., help="Workflow UUID."),
    status: Optional[str] = typer.Option(None, "--status"),
    limit: int = typer.Option(50, "--limit"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """List past runs for a workflow."""
    typer.echo("workflows runs: not implemented yet -- Fern SDK regen pending", err=True)
    sys.exit(1)
