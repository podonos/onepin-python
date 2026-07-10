"""Hand-written composite commands that don't fit the table-driven dispatcher.

These have bespoke control flow (polling, file I/O, multi-step S3 upload, local schema
emit) that the declarative TABLE cannot express. Each lazy-imports the SDK context so the
fast-startup guarantee holds.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

import typer

from onepin._cli._ctx import CliError, api_errors, get_client, output_json, to_jsonable
from onepin._cli.render import render_json

# Run states that end polling. SDK reports run status as a raw str (no enum to import);
# this is the documented drift risk, covered by the SDK contract test.
TERMINAL_RUN_STATES = frozenset({"completed", "failed", "cancelled"})


# === workflows run [--watch] =============================================================


def workflow_run(
    workflow_id: str = typer.Argument(..., help="Workflow UUID."),
    script: Optional[str] = typer.Option(
        None, "--script", help="Run-scoped script text; overrides the saved script for this run only."
    ),
    source_language: Optional[str] = typer.Option(
        None, "--source-language", help="BCP-47 language of --script (e.g. en-us); defaults to the saved language."
    ),
    watch: bool = typer.Option(False, "--watch", help="Poll run status until a terminal state."),
    timeout: float = typer.Option(300.0, "--timeout", help="Max seconds to watch before giving up."),
    json_output_local: bool = typer.Option(False, "--json", help="Emit JSON instead of text."),
) -> None:
    """Start a workflow run, optionally polling until it finishes.

    Without ``--watch``, prints the started run and exits. With ``--watch``, polls
    ``runs.status`` every 2s up to ``--timeout`` seconds; a terminal state exits 0
    (or 1 if failed), a timeout exits 1, and Ctrl-C prints the last status and exits 130.
    """
    json_on = output_json(json_output_local)
    with api_errors(json_on):
        client = get_client()
        kwargs = _maybe_workspace(client.workflows.runs.start)
        # Run-scoped inputs ride as additional body parameters until the generated
        # start() gains script_text/source_language on the next spec regen — the wire
        # format is identical either way, so this keeps working after the regen too.
        overrides = {
            key: value
            for key, value in (("script_text", script), ("source_language", source_language))
            if value is not None
        }
        if overrides:
            kwargs["request_options"] = {"additional_body_parameters": overrides}
        started = client.workflows.runs.start(workflow_id, **kwargs)
        run = to_jsonable(getattr(started, "data", started))
        run_id = run.get("id") if isinstance(run, dict) else None

        if not watch or run_id is None:
            _emit_run(run, json_on, "Started run {id}.")
            return

        deadline = time.monotonic() + timeout
        last = run
        try:
            while True:
                status = last.get("status") if isinstance(last, dict) else None
                if status in TERMINAL_RUN_STATES:
                    break
                if time.monotonic() >= deadline:
                    _emit_run_error("TIMEOUT", "Timed out watching run.", last, json_on, "Timed out watching run {id}.")
                    raise SystemExit(1)
                time.sleep(2)
                status_kwargs = _maybe_workspace(client.workflows.runs.status)
                resp = client.workflows.runs.status(workflow_id, run_id, **status_kwargs)
                last = to_jsonable(getattr(resp, "data", resp))
        except KeyboardInterrupt:
            _emit_run_error("INTERRUPTED", "Interrupted.", last, json_on, "Interrupted while watching run {id}.")
            raise SystemExit(130) from None

        _emit_run(last, json_on, "Run {id} finished: {status}.")
        if isinstance(last, dict) and last.get("status") == "failed":
            raise SystemExit(1)


def _emit_run_error(
    code: str,
    message: str,
    run: Any,
    json_on: bool,
    template: str,
) -> None:
    """Emit a watch-mode failure (timeout / interrupt) as a structured error or plain text."""
    import sys

    context = run if isinstance(run, dict) else {}
    status = context.get("status", "")
    if json_on:
        envelope: dict[str, Any] = {
            "error": {"code": code, "message": message},
            "meta": {"last_status": status},
        }
        print(json.dumps(envelope, indent=2, default=str), file=sys.stderr)
    else:
        typer.echo(template.format(id=context.get("id", ""), status=status), err=True)


def _emit_run(run: Any, json_on: bool, template: str) -> None:
    """Emit a successful watch-mode result."""
    if json_on:
        render_json(run)
        return
    context = run if isinstance(run, dict) else {}
    typer.echo(template.format(id=context.get("id", ""), status=context.get("status", "")))


# === uploads create ======================================================================


def upload_create(
    file: str = typer.Option(..., "--file", help="Path to the file to upload."),
    category: str = typer.Option(..., "--category", help="Upload category: script or dictionary."),
    json_output_local: bool = typer.Option(False, "--json", help="Emit JSON instead of text."),
) -> None:
    """Upload a file via the presigned-S3 flow (create -> PUT bytes).

    Reads the whole file into memory (large-file streaming is out of scope), requests a
    presigned URL, and PUTs the bytes. Prints the upload id; run ``uploads confirm`` next.
    """
    import httpx

    json_on = output_json(json_output_local)
    if category not in ("script", "dictionary"):
        with api_errors(json_on):
            raise CliError("INVALID_CATEGORY", "Category must be 'script' or 'dictionary'.")

    path = Path(file)
    with api_errors(json_on):
        try:
            payload = path.read_bytes()
        except (FileNotFoundError, IsADirectoryError) as exc:
            raise CliError("FILE_NOT_FOUND", f"File not found: {file}") from exc
        except PermissionError as exc:
            raise CliError("PERMISSION_DENIED", f"Permission denied: {file}") from exc

        client = get_client()
        create_kwargs = _maybe_workspace(client.uploads.create)
        created = client.uploads.create(filename=path.name, category=category, **create_kwargs)
        data = getattr(created, "data", created)
        upload = getattr(data, "upload", None)
        upload_url = getattr(data, "upload_url", None)
        if upload is None or not upload_url:
            raise CliError("UPLOAD_FAILED", "Server did not return a presigned upload URL.")
        content_type = getattr(upload, "content_type", None) or "application/octet-stream"
        upload_id = getattr(upload, "id", None)

        try:
            put = httpx.put(upload_url, content=payload, headers={"Content-Type": content_type}, timeout=60.0)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise CliError("UPLOAD_FAILED", f"Could not upload to storage: {exc}") from exc
        if put.status_code >= 400:
            raise CliError(
                "UPLOAD_FAILED",
                f"Storage rejected the upload (HTTP {put.status_code}). The presigned URL may have expired.",
            )

        if json_on:
            render_json({"ok": True, "id": upload_id})
        else:
            typer.echo(f"Uploaded {path.name} as upload {upload_id}. Run `onepin uploads confirm {upload_id}`.")


# === workflows runs download / download-node =============================================


def run_download(
    workflow_id: str = typer.Argument(..., help="Workflow UUID."),
    run_id: str = typer.Argument(..., help="Run UUID."),
    out: str = typer.Option(..., "--out", help="Destination file path (required)."),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing file."),
    json_output_local: bool = typer.Option(False, "--json", help="Emit JSON instead of text."),
) -> None:
    """Download a run's full export to ``--out`` (atomic write, refuses to clobber without --force)."""
    _download(workflow_id, run_id, None, out, force, json_output_local)


def run_download_node(
    workflow_id: str = typer.Argument(..., help="Workflow UUID."),
    run_id: str = typer.Argument(..., help="Run UUID."),
    node_id: str = typer.Argument(..., help="Node UUID."),
    out: str = typer.Option(..., "--out", help="Destination file path (required)."),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing file."),
    json_output_local: bool = typer.Option(False, "--json", help="Emit JSON instead of text."),
) -> None:
    """Download a single node's output to ``--out`` (atomic write, refuses to clobber without --force)."""
    _download(workflow_id, run_id, node_id, out, force, json_output_local)


def _download(
    workflow_id: str,
    run_id: str,
    node_id: Optional[str],
    out: str,
    force: bool,
    json_output_local: bool,
) -> None:
    import httpx

    json_on = output_json(json_output_local)
    dest = Path(out)
    with api_errors(json_on):
        # Early check for human UX (fast fail before network round-trip). The real
        # clobber guard is the atomic O_CREAT|O_EXCL reservation inside _atomic_write.
        if dest.exists() and not force:
            raise CliError("FILE_EXISTS", f"{out} already exists. Pass --force to overwrite.")

        client = get_client()
        if node_id is None:
            method = client.workflows.download_run
            resp = method(workflow_id, run_id, **_maybe_workspace(method))
        else:
            method = client.workflows.download_run_node
            resp = method(workflow_id, run_id, node_id, **_maybe_workspace(method))
        data = getattr(resp, "data", resp)
        url = getattr(data, "url", None)
        if not url:
            raise CliError("DOWNLOAD_FAILED", "Server did not return a download URL.")

        try:
            response = httpx.get(url, timeout=60.0, follow_redirects=True)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise CliError("DOWNLOAD_FAILED", f"Could not download: {exc}") from exc
        if response.status_code >= 400:
            raise CliError(
                "DOWNLOAD_FAILED",
                f"Download failed (HTTP {response.status_code}). The download URL may have expired.",
            )

        _atomic_write(dest, response.content, force=force)

        if json_on:
            render_json({"ok": True, "path": str(dest)})
        else:
            typer.echo(f"Wrote {len(response.content)} bytes to {dest}.")


def _atomic_write(dest: Path, content: bytes, *, force: bool) -> None:
    """Write ``content`` to ``dest`` atomically, refusing to clobber without --force.

    Delegates the TOCTOU-safe write idiom to :func:`onepin._cli._fsutil.atomic_write_bytes`
    and maps its builtin exceptions to this command's stable error codes.
    """
    from onepin._cli import _fsutil

    try:
        _fsutil.atomic_write_bytes(dest, content, force=force)
    except FileExistsError as exc:
        raise CliError("FILE_EXISTS", f"{dest} already exists. Pass --force to overwrite.") from exc
    except (FileNotFoundError, NotADirectoryError) as exc:
        raise CliError("DOWNLOAD_FAILED", f"Destination directory does not exist: {dest.parent}") from exc
    except OSError as exc:
        raise CliError("DOWNLOAD_FAILED", f"Could not write {dest}: {exc}") from exc


# === workflows definition-schema (pure local) ============================================


def definition_schema(
    json_output_local: bool = typer.Option(False, "--json", help="Emit JSON (default for this command)."),
) -> None:
    """Print the JSON Schema for a workflow definition (graph + execution).

    Use with ``workflows create --definition @file.json`` to author a valid definition.
    """
    from onepin.types import WorkflowDefinitionInput

    schema = WorkflowDefinitionInput.model_json_schema()
    render_json(schema)


# === Shared helpers ======================================================================


def _maybe_workspace(method: Any) -> dict[str, Any]:
    """Return ``{"workspace_id": ...}`` only if the SDK method accepts it and the flag is set.

    Reuses the dispatcher's ``_accepts_workspace_kwarg`` so there is a single rule for
    distinguishing the scoping keyword-only ``workspace_id`` from a positional path param.
    """
    from onepin._cli import _state
    from onepin._cli._dispatch import _accepts_workspace_kwarg

    workspace = _state.root_options.get("workspace")
    if not workspace:
        return {}
    if _accepts_workspace_kwarg(method):
        return {"workspace_id": workspace}
    return {}
