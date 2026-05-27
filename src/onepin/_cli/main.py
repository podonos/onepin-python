"""OnePin CLI entry point -- `onepin = "onepin._cli.main:app"`."""
from __future__ import annotations

import typer

from onepin import __version__
from onepin._cli.commands import _registry

app = typer.Typer(
    name="onepin",
    help="OnePin Python SDK CLI.",
    no_args_is_help=True,
    rich_markup_mode="markdown",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"onepin {__version__}")
        raise typer.Exit()


@app.callback()
def _main(
    version: bool = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
    api_key: str | None = typer.Option(None, "--api-key", envvar="ONEPIN_API_KEY"),
    base_url: str | None = typer.Option(None, "--base-url", envvar="ONEPIN_BASE_URL"),
    workspace: str | None = typer.Option(None, "--workspace"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON instead of rich tables."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable ANSI coloring."),
    verbose: bool = typer.Option(False, "-v", "--verbose"),
    debug: bool = typer.Option(False, "--debug"),
) -> None:
    """OnePin CLI -- control workflows, voices, templates, and uploads from your terminal."""


_registry.register(app)
