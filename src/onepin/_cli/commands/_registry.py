"""Wire subcommands into the root Typer app."""

from __future__ import annotations

import typer

from onepin._cli.commands import auth, templates, uploads, voices, workflows


def register(app: typer.Typer) -> None:
    app.command(name="login")(auth.login)
    app.command(name="logout")(auth.logout)
    app.command(name="whoami")(auth.whoami)
    app.add_typer(workflows.app, name="workflows")
    app.add_typer(voices.app, name="voices")
    app.add_typer(templates.app, name="templates")
    app.add_typer(uploads.app, name="uploads")
