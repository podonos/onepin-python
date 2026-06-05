"""Unit tests for registry assembly helpers."""

from __future__ import annotations

import typer

from onepin._cli.commands import _registry


def test_find_subgroup_returns_none_when_absent() -> None:
    parent = typer.Typer()
    assert _registry._find_subgroup(parent, "nope") is None


def test_find_subgroup_finds_registered() -> None:
    parent = typer.Typer()
    child = typer.Typer()
    parent.add_typer(child, name="runs")
    assert _registry._find_subgroup(parent, "runs") is child


def test_register_is_idempotent_shape() -> None:
    # Registering onto a fresh app wires every top-level group + auth + schema.
    app = typer.Typer()
    _registry.register(app)
    cli = typer.main.get_command(app)
    import click

    ctx = click.Context(cli)
    names = set(cli.list_commands(ctx))
    assert {"login", "logout", "whoami", "schema", "skill", "workflows", "provider-keys", "health"} <= names


def test_skill_group_has_install_path_uninstall() -> None:
    import click

    app = typer.Typer()
    _registry.register(app)
    cli = typer.main.get_command(app)
    ctx = click.Context(cli)
    skill_group = cli.get_command(ctx, "skill")
    assert skill_group is not None
    sub = set(skill_group.list_commands(click.Context(skill_group)))
    assert {"install", "path", "uninstall"} <= sub
