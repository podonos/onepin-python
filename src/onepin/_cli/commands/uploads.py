"""Upload commands (3-step presigned flow). Implementation pending first Fern SDK regen."""

from __future__ import annotations

import sys

import typer

app = typer.Typer(help="Manage file uploads.", no_args_is_help=True)


@app.command(name="create")
def create_upload(
    file: str = typer.Option(..., "--file", help="Path to file to upload."),
    category: str = typer.Option(..., "--category", help="Upload category: script or dictionary."),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Upload a file via presigned S3 URL (step 1 of 3).

    Steps:
      1. POST /api/v1/uploads to get a presigned S3 PUT URL
      2. PUT file bytes directly to S3
      3. Prints upload_id -- caller must run `confirm` to finalize

    Categories: script (.txt, .docx) or dictionary (.csv).
    """
    typer.echo("uploads create: not implemented yet -- Fern SDK regen pending", err=True)
    sys.exit(1)


@app.command(name="confirm")
def confirm_upload(
    upload_id: str = typer.Argument(..., help="Upload UUID returned by `create`."),
    workflow_id: str = typer.Option(..., "--workflow-id", help="Workflow UUID to attach upload to."),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Confirm an upload and attach it to a workflow (step 2 of 3).

    Calls POST /api/v1/uploads/{upload_id} with context_type=workflow.
    """
    typer.echo("uploads confirm: not implemented yet -- Fern SDK regen pending", err=True)
    sys.exit(1)


@app.command(name="delete")
def delete_upload(
    upload_id: str = typer.Argument(..., help="Upload UUID to delete."),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Delete an upload and release storage quota."""
    typer.echo("uploads delete: not implemented yet -- Fern SDK regen pending", err=True)
    sys.exit(1)
