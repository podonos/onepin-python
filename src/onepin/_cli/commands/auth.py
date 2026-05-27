"""Login / logout / whoami commands. Implementation pending first Fern SDK regen."""
from __future__ import annotations

import sys

import typer


def login(
    key: str | None = typer.Option(None, "--key", help="API key. Prompts if omitted."),
    base_url: str | None = typer.Option(None, "--base-url"),
) -> None:
    """Validate an API key and write it to ~/.onepin/credentials."""
    typer.echo("login: not implemented yet -- Fern SDK regen pending", err=True)
    sys.exit(1)


def logout() -> None:
    """Remove ~/.onepin/credentials."""
    typer.echo("logout: not implemented yet -- Fern SDK regen pending", err=True)
    sys.exit(1)


def whoami() -> None:
    """Show active auth source + workspace UUID + scopes."""
    typer.echo("whoami: not implemented yet -- Fern SDK regen pending", err=True)
    sys.exit(1)
