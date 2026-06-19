"""OnePin CLI entry point -- `onepin = "onepin._cli.main:app"`."""

from __future__ import annotations

import os

import click
import typer

from onepin._cli import __version__, _state
from onepin._cli.commands import _registry

app = typer.Typer(
    name="onepin",
    help="Onepin Python SDK CLI.",
    invoke_without_command=True,
    no_args_is_help=True,
    rich_markup_mode="markdown",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"onepin {__version__}")
        raise typer.Exit()


def _root_option_callback(name: str, value: object) -> object:
    ctx = click.get_current_context(silent=True)
    _state.root_options[name] = value
    _state.root_options[f"{name}_source"] = ctx.get_parameter_source(name) if ctx is not None else None
    return value


def _no_color_callback(value: bool) -> bool:
    # NO_COLOR is the one signal Rich, Click, and Typer all honor (W3C). Set it eagerly
    # so it lands before help/usage/error rendering -- otherwise --no-color only reaches
    # our own render.py output, not library-rendered text. Tests reset it (conftest).
    if value:
        os.environ["NO_COLOR"] = "1"
    return value


@app.callback()
def _main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
    api_key: str | None = typer.Option(
        None,
        "--api-key",
        envvar="ONEPIN_API_KEY",
        callback=lambda value: _root_option_callback("api_key", value),
        is_eager=True,
    ),
    base_url: str | None = typer.Option(
        None,
        "--base-url",
        envvar="ONEPIN_BASE_URL",
        callback=lambda value: _root_option_callback("base_url", value),
        is_eager=True,
    ),
    workspace: str | None = typer.Option(
        None,
        "--workspace",
        envvar="ONEPIN_WORKSPACE_ID",
        help="Workspace UUID to scope requests to (forwarded to commands that accept it).",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit JSON instead of rich tables.",
        callback=lambda value: _root_option_callback("json_output", value),
        is_eager=True,
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable ANSI coloring.",
        is_eager=True,
        callback=_no_color_callback,
    ),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Log HTTP requests/responses to stderr."),
    debug: bool = typer.Option(False, "--debug", help="Enable verbose logging (implies --verbose)."),
) -> None:
    """Onepin CLI -- control workflows, voices, templates, and uploads from your terminal."""
    _state.root_options = {
        "api_key": api_key,
        "api_key_source": ctx.get_parameter_source("api_key"),
        "base_url": base_url,
        "base_url_source": ctx.get_parameter_source("base_url"),
        "workspace": workspace,
        "json_output": json_output,
        "no_color": no_color,
        # --debug implies --verbose (per the documented flag contract).
        "verbose": verbose or debug,
        "debug": debug,
    }


_registry.register(app)
