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
        overrides = _run_scoped_body(script, source_language)
        if overrides is not None:
            kwargs["request_options"] = overrides
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


# === workflows preview-run ===============================================================


def workflow_preview_run(
    workflow_id: str = typer.Argument(..., help="Workflow UUID."),
    script: Optional[str] = typer.Option(
        None, "--script", help="Price this script text instead of the saved one (same as `run --script`)."
    ),
    source_language: Optional[str] = typer.Option(
        None, "--source-language", help="BCP-47 language of --script (e.g. en-us); defaults to the saved language."
    ),
    json_output_local: bool = typer.Option(False, "--json", help="Emit JSON instead of text."),
) -> None:
    """Estimate the credit cost of a run without executing it.

    Takes the same run-scoped overrides as ``workflows run``, and for the same reason: a
    workflow whose script node is empty is *valid to run* with ``--script`` but cannot be
    priced without it (the estimate has no text to count, so the server answers
    ``VALIDATION_ERROR``). Passing the same ``--script``/``--source-language`` you intend to
    run prices the operation that will actually be charged, rather than the saved definition
    that will not.

    No run is created and no credits are consumed.
    """
    from onepin._cli._dispatch import _render_keyvalue

    json_on = output_json(json_output_local)
    with api_errors(json_on):
        client = get_client()
        kwargs = _maybe_workspace(client.workflows.preview_run)
        overrides = _run_scoped_body(script, source_language)
        if overrides is not None:
            kwargs["request_options"] = overrides
        resp = client.workflows.preview_run(workflow_id, **kwargs)
        payload = to_jsonable(getattr(resp, "data", resp))
        if json_on:
            render_json(payload)
            return
        _render_keyvalue(payload)


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


# === workflows set-voice =================================================================

_GENERATOR_TYPE = "operator_generator"


def workflow_set_voice(
    workflow_id: str = typer.Argument(..., help="Workflow UUID."),
    locale: str = typer.Option(..., "--locale", help="BCP-47 locale slot to assign (e.g. ko-kr)."),
    voice: str = typer.Option(..., "--voice", help="Catalog voice UUID (the `id` column of `voices list`)."),
    model: Optional[str] = typer.Option(None, "--model", help="TTS model; defaults to one that supports the locale."),
    node_id: Optional[str] = typer.Option(None, "--node-id", help="Generator node, when the graph has several."),
    json_output_local: bool = typer.Option(False, "--json", help="Emit JSON instead of text."),
) -> None:
    """Point one locale of a workflow's generator at a different voice.

    This is a **permanent edit to the saved workflow** — every future run uses the new voice,
    and there is no run-scoped voice override to reach for instead. Duplicate the workflow
    first if the original has to survive.

    It exists so that changing a voice does not require reading the whole definition out,
    editing a nested map by hand and writing all of it back: that path rewrites every node on
    every edit, and a single mistake in it costs the user their graph. Here only the one
    `voice_map` entry moves. The previous assignment is printed, so the change is visible and
    can be put back.
    """
    json_on = output_json(json_output_local)
    with api_errors(json_on):
        client = get_client()
        current = client.workflows.get(workflow_id, **_maybe_workspace(client.workflows.get))
        workflow = to_jsonable(getattr(current, "data", current)) or {}
        definition = workflow.get("definition") or {}
        node = _generator_node(definition, node_id)

        voice_row = to_jsonable(getattr(client.voices.get(voice, **_maybe_workspace(client.voices.get)), "data", None))
        assignment = _voice_assignment(voice_row, locale, model)

        config = node.setdefault("config", {}) or {}
        node["config"] = config
        voice_map = dict(config.get("voice_map") or {})
        previous = voice_map.get(locale)
        voice_map[locale] = [assignment]
        config["voice_map"] = voice_map

        updated = client.workflows.patch_workflow(
            workflow_id, definition=definition, **_maybe_workspace(client.workflows.patch_workflow)
        )
        result = to_jsonable(getattr(updated, "data", updated))

        if json_on:
            render_json(
                {
                    "workflow": result,
                    "node_id": node.get("id"),
                    "locale": locale,
                    "voice": assignment,
                    "previous": previous,
                }
            )
            return
        typer.echo(
            f"Set {locale} to {assignment['voice_name']} "
            f"({assignment['provider']}/{assignment['model']}) on node {node.get('id')}."
        )
        typer.echo(f"Previous: {_describe_assignment(previous)}")
        typer.echo("This changed the saved workflow; every future run uses the new voice.")


def _generator_node(definition: dict[str, Any], node_id: Optional[str]) -> dict[str, Any]:
    """Locate the generator node to edit, refusing to guess when the graph has more than one."""
    nodes: list[dict[str, Any]] = ((definition.get("graph") or {}).get("nodes")) or []
    generators = [node for node in nodes if node.get("type") == _GENERATOR_TYPE]
    if node_id is not None:
        for node in generators:
            if node.get("id") == node_id:
                return node
        known = ", ".join(str(node.get("id")) for node in generators) or "none"
        raise CliError("NOT_FOUND", f"No {_GENERATOR_TYPE} node {node_id} in this workflow. Present: {known}.")
    if not generators:
        raise CliError("NOT_FOUND", f"This workflow has no {_GENERATOR_TYPE} node, so it has no voice to set.")
    if len(generators) > 1:
        ids = ", ".join(str(node.get("id")) for node in generators)
        raise CliError("AMBIGUOUS_NODE", f"This workflow has {len(generators)} generators; pass --node-id ({ids}).")
    return generators[0]


def _locale_supported(locale: str, declared: list[str]) -> bool:
    """True when ``locale`` is covered by a declared locale list, family-aware.

    A declared list carries whatever the voice registered, and a bare family is a legal
    entry: the API counts ``ko`` as official because ``ko-kr`` is, and ``voices list
    --language ko-kr`` returns voices that declared only ``ko``. Exact-matching here would
    reject, with "does not support ko-kr", precisely the voices the discovery command just
    recommended — and leave the hand-edited ``workflows update --definition`` path as the
    only way to assign them, which is what this command exists to avoid.
    """
    wanted = locale.casefold()
    family = wanted.split("-", 1)[0]
    for entry in declared:
        declared_locale = str(entry).casefold()
        if declared_locale == wanted or declared_locale == family:
            return True
        # A declared region also covers a bare family asked for: `ko` against `ko-kr`.
        if declared_locale.split("-", 1)[0] == wanted:
            return True
    return False


def _voice_assignment(voice_row: Optional[dict[str, Any]], locale: str, model: Optional[str]) -> dict[str, Any]:
    """Build a VoiceAssignment from a catalog row, checking it can actually speak the locale.

    The two id fields are not interchangeable and getting them backwards is the classic way to
    write a definition that saves and then fails at run time: ``voice_id`` is the provider's own
    id, ``catalog_voice_id`` is the catalog UUID the caller passed.
    """
    if not voice_row:
        raise CliError("NOT_FOUND", "Voice not found.")
    if voice_row.get("is_active") is False:
        raise CliError("VALIDATION_ERROR", f"Voice {voice_row.get('name')} is not active and cannot be assigned.")

    supported = voice_row.get("supported_languages") or []
    if supported and not _locale_supported(locale, supported):
        raise CliError(
            "VALIDATION_ERROR",
            f"{voice_row.get('name')} does not support {locale}. It supports: {', '.join(supported)}.",
        )

    capabilities = voice_row.get("model_capabilities") or []
    chosen = model or _default_model(capabilities, voice_row, locale)
    _check_model(capabilities, chosen, locale, voice_row)

    return {
        "voice_id": voice_row["provider_voice_id"],
        "catalog_voice_id": voice_row["id"],
        "provider": voice_row["provider"],
        "model": chosen,
        "voice_name": voice_row.get("name"),
    }


def _default_model(capabilities: list[dict[str, Any]], voice_row: dict[str, Any], locale: str) -> str:
    """First model that covers the locale; a model with unknown coverage is a last resort."""
    for capability in capabilities:
        if _locale_supported(locale, capability.get("supported_languages") or []):
            return str(capability["model"])
    for capability in capabilities:
        if not capability.get("languages_known"):
            return str(capability["model"])
    models = voice_row.get("supported_models") or []
    if models:
        return str(models[0])
    raise CliError("VALIDATION_ERROR", f"{voice_row.get('name')} lists no usable model for {locale}.")


def _check_model(capabilities: list[dict[str, Any]], model: str, locale: str, voice_row: dict[str, Any]) -> None:
    """Reject a model that is known not to cover the locale; stay quiet when coverage is unknown."""
    for capability in capabilities:
        if capability.get("model") != model:
            continue
        languages = capability.get("supported_languages") or []
        # languages_known=False means the API cannot enumerate coverage — not that there is none.
        if capability.get("languages_known") and not _locale_supported(locale, languages):
            raise CliError(
                "VALIDATION_ERROR",
                f"Model {model} does not cover {locale} for {voice_row.get('name')}"
                + (f" (it covers: {', '.join(languages)})." if languages else "."),
            )
        return
    known = ", ".join(str(capability.get("model")) for capability in capabilities)
    if known:
        raise CliError("VALIDATION_ERROR", f"{voice_row.get('name')} has no model {model}. It has: {known}.")


def _describe_assignment(previous: Any) -> str:
    """Describe the assignment(s) being replaced, so they can be restored.

    A locale slot holds a *list* of ``VoiceAssignment``, not one, and this command replaces
    the whole list. Printing only the first entry would quietly lose the rest: the caller is
    told the change is reversible, so every entry that was there has to be in the line that
    says what was there.
    """
    if not previous:
        return "nothing (this locale had no voice assigned)."
    entries = previous if isinstance(previous, list) else [previous]
    if not all(isinstance(entry, dict) for entry in entries):
        return json.dumps(previous, default=str)
    return "; ".join(_describe_entry(entry) for entry in entries) + "."


def _describe_entry(entry: dict[str, Any]) -> str:
    name = entry.get("voice_name") or entry.get("catalog_voice_id") or entry.get("voice_id")
    return f"{name} ({entry.get('provider')}/{entry.get('model')}), catalog id {entry.get('catalog_voice_id')}"


# === workflows duplicate =================================================================


def workflow_duplicate(
    workflow_id: str = typer.Argument(..., help="Workflow UUID."),
    name: Optional[str] = typer.Option(None, "--name", help="Name for the copy (default: the original + ' (Copy)')."),
    json_output_local: bool = typer.Option(False, "--json", help="Emit JSON instead of text."),
) -> None:
    """Copy a workflow, optionally naming the copy.

    Duplicating is the way to change a saved voice without touching the original, so the copies
    accumulate — and the API names every one of them ``<original> (Copy)``, which makes a list of
    them indistinguishable. ``--name`` is applied as a follow-up patch because the duplicate
    endpoint takes no name.
    """
    json_on = output_json(json_output_local)
    with api_errors(json_on):
        if name is not None and not name.strip():
            # Validate before duplicating, not after: a blank name that surfaced later would
            # leave a stray copy behind. Distinguishing "not passed" from "passed empty" also
            # keeps --name "" from silently reporting a rename that never happened.
            raise CliError("INVALID_ARGUMENTS", "--name must not be blank.")

        client = get_client()
        created = client.workflows.duplicate_workflow(
            workflow_id, **_maybe_workspace(client.workflows.duplicate_workflow)
        )
        workflow = to_jsonable(getattr(created, "data", created))
        new_id = workflow.get("id") if isinstance(workflow, dict) else None

        if name is not None and new_id:
            try:
                renamed = client.workflows.patch_workflow(
                    new_id, name=name, **_maybe_workspace(client.workflows.patch_workflow)
                )
            except Exception as exc:  # noqa: BLE001 - the copy exists; its id must not be lost
                # Two calls, no transaction. Naming the id is the difference between a copy the
                # user can find and fix, and an orphan they have to go hunting for.
                raise CliError(
                    "RENAME_FAILED",
                    f"Duplicated into {new_id}, but renaming it failed: {exc}. The copy exists under its default name.",
                ) from exc
            workflow = to_jsonable(getattr(renamed, "data", renamed))

        if json_on:
            render_json(workflow)
        else:
            typer.echo(f"Duplicated workflow into {workflow.get('id', '')}.")


# === voices sample =======================================================================

# Extensions for the content types the preview endpoint reports. Anything else falls back to
# the URL's own suffix, then to .mp3 — the sample is still written, just named conservatively.
_AUDIO_EXTENSIONS = {
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/wave": ".wav",
    "audio/ogg": ".ogg",
    "audio/webm": ".webm",
    "audio/flac": ".flac",
    "audio/aac": ".aac",
}


def voices_sample(
    voice_ids: list[str] = typer.Argument(..., help="One or more voice UUIDs to audition."),
    language: Optional[str] = typer.Option(
        None, "--language", help="BCP-47 locale to hear the voice in (e.g. ko-kr). Falls back to its default sample."
    ),
    model: Optional[str] = typer.Option(None, "--model", help="Prefer a specific TTS model (e.g. sonic-2)."),
    out: Optional[str] = typer.Option(None, "--out", help="Write a single sample to this file path."),
    out_dir: Optional[str] = typer.Option(None, "--out-dir", help="Write one file per voice into this directory."),
    play: bool = typer.Option(False, "--play", help="Play each sample with the OS audio player."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files."),
    json_output_local: bool = typer.Option(False, "--json", help="Emit JSON instead of text."),
) -> None:
    """Fetch (and optionally play) voice preview audio, for several voices in one call.

    A voice is chosen by ear, and a tag list is not an audition: passing every shortlisted id
    at once is what makes comparing them practical. Each sample URL is minted fresh by this
    command and is valid for about an hour, so an expired link is re-signed by running it
    again rather than by hunting for a refresh flag.

    ``--play`` names each voice on its own line immediately before its clip starts, because a
    shortlist played in one call is otherwise a run of anonymous audio; a summary printed once
    the sound has stopped names them too late to be of any use.

    With neither ``--out``/``--out-dir`` nor ``--play`` it prints what it found — name, the
    locale actually served, the model, and the URL — which is also the shape to hand to a user
    when there is no audio device.
    """
    json_on = output_json(json_output_local)
    with api_errors(json_on):
        if out and out_dir:
            raise CliError("INVALID_ARGUMENTS", "Pass either --out or --out-dir, not both.")
        if out and len(voice_ids) > 1:
            raise CliError(
                "INVALID_ARGUMENTS",
                f"--out names a single file but {len(voice_ids)} voices were given; use --out-dir.",
            )
        if out_dir and not Path(out_dir).is_dir():
            raise CliError("DIRECTORY_NOT_FOUND", f"Directory does not exist: {out_dir}")

        client = get_client()
        rows = [_voice_sample_row(client, voice_id, language, model) for voice_id in voice_ids]

        destinations = _sample_destinations(rows, out, out_dir, play)
        for row, destination in zip(rows, destinations, strict=True):
            if destination is not None:
                row["path"] = str(_write_sample(row["sample_url"], destination, force=force))

        if play:
            total = len(rows)
            for index, row in enumerate(rows, start=1):
                # Named *before* its clip, not in a summary afterwards: a shortlist played in one
                # call is only followable by ear if the label lands while that voice is speaking.
                if not json_on:
                    typer.echo(f"Playing {index}/{total} {_sample_label(row)}: {row['path']}")
                _play_audio(Path(row["path"]), json_on)
            if json_on:
                render_json(rows)
            return

        _emit_samples(rows, json_on)


def _voice_sample_row(client: Any, voice_id: str, language: Optional[str], model: Optional[str]) -> dict[str, Any]:
    """Resolve one voice to a playable sample, falling back to its default sample.

    ``voices.preview`` is per-locale and 404s when a voice has no preview recorded *in that
    locale* — which is not the same claim as "this voice cannot speak it" (``supported_languages``
    is the claim about ability; ``preview_locales`` is what this endpoint will serve). So a 404
    degrades to the voice's own ``sample_url``, in whatever language that happens to be, and the
    row records the substitution so the caller can say so rather than mislabel what was heard.
    """
    from onepin._cli._dispatch import _is_not_found

    if language is not None:
        preview_kwargs = _maybe_workspace(client.voices.preview)
        try:
            resp = client.voices.preview(voice_id, language=language, model=model, **preview_kwargs)
        except Exception as exc:  # noqa: BLE001 - only a 404 degrades; everything else propagates
            # The endpoint declares 422 only, so Fern raises a bare ApiError for 404 rather than
            # NotFoundError — match on the status, not the class.
            if not _is_not_found(exc):
                raise
        else:
            data = to_jsonable(getattr(resp, "data", resp))
            return {
                "voice_id": voice_id,
                "name": data.get("name"),
                "locale": data.get("locale"),
                "model": data.get("model"),
                "sample_url": data.get("sample_url"),
                "content_type": data.get("content_type"),
                "fallback": False,
            }

    get_kwargs = _maybe_workspace(client.voices.get)
    data = to_jsonable(getattr(client.voices.get(voice_id, **get_kwargs), "data", None))
    sample_url = (data or {}).get("sample_url")
    if not sample_url:
        raise CliError(
            "NO_SAMPLE",
            f"No preview audio for voice {voice_id}"
            + (f" in {language}, and it has no default sample either." if language else "."),
        )
    return {
        "voice_id": voice_id,
        "name": (data or {}).get("name"),
        # The default sample does not follow --language; report what it is, not what was asked.
        "locale": (data or {}).get("language_sample_locale"),
        "model": None,
        "sample_url": sample_url,
        "content_type": None,
        "fallback": language is not None,
    }


def _sample_destinations(
    rows: list[dict[str, Any]], out: Optional[str], out_dir: Optional[str], play: bool
) -> list[Optional[Path]]:
    """Plan where every row's audio lands, resolving name collisions before anything is written.

    Voice display names are not unique — two providers both ship a "Sarah" — so a stem built
    from name + locale collides, and the loop would write both rows to one path, report two
    files, and exit 0 having silently dropped one sample. Stems are therefore planned as a set:
    only the ones that actually collide get their voice id appended, so the common case keeps
    readable filenames and no row can overwrite another.
    """
    if out:
        return [Path(out)] * len(rows)
    if not out_dir and not play:
        return [None] * len(rows)

    stems = [_sample_stem(row) for row in rows]
    duplicated = {stem for stem in stems if stems.count(stem) > 1}
    names = [
        f"{stem}-{row['voice_id']}{_audio_extension(row)}" if stem in duplicated else f"{stem}{_audio_extension(row)}"
        for stem, row in zip(stems, rows, strict=True)
    ]
    if out_dir:
        return [Path(out_dir) / name for name in names]

    # Play-only: throwaway files, because the macOS player takes a path and not a URL. One
    # directory for the whole invocation rather than one per row — the paths are reported to
    # the caller and so have to outlive the process, which makes every one of them a leak;
    # auditioning a five-voice shortlist should cost one of them, not five.
    import tempfile

    scratch = Path(tempfile.mkdtemp(prefix="onepin-sample-"))
    return [scratch / name for name in names]


def _sample_stem(row: dict[str, Any]) -> str:
    """A filesystem-safe stem from the voice name + locale, falling back to the id.

    The name is server-supplied and can carry separators or spaces, so it is filtered down to
    a conservative character set rather than trusted into a path.
    """
    parts = [str(row.get("name") or ""), str(row.get("locale") or "")]
    raw = "-".join(part for part in parts if part)
    safe = "".join(char if char.isalnum() or char in "._-" else "-" for char in raw).strip("-.")
    return safe or str(row["voice_id"])


def _audio_extension(row: dict[str, Any]) -> str:
    content_type = (row.get("content_type") or "").split(";")[0].strip().lower()
    if content_type in _AUDIO_EXTENSIONS:
        return _AUDIO_EXTENSIONS[content_type]
    suffix = Path(str(row["sample_url"]).split("?", 1)[0]).suffix.lower()
    return suffix if suffix in set(_AUDIO_EXTENSIONS.values()) else ".mp3"


def _write_sample(url: str, dest: Path, *, force: bool) -> Path:
    import httpx

    if dest.exists() and not force:
        raise CliError("FILE_EXISTS", f"{dest} already exists. Pass --force to overwrite.")
    try:
        response = httpx.get(url, timeout=60.0, follow_redirects=True)
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        raise CliError("DOWNLOAD_FAILED", f"Could not download sample: {exc}") from exc
    if response.status_code >= 400:
        raise CliError(
            "DOWNLOAD_FAILED",
            f"Sample download failed (HTTP {response.status_code}). The presigned URL may have expired.",
        )
    _atomic_write(dest, response.content, force=force)
    return dest


def _play_audio(path: Path, json_on: bool) -> None:
    """Play ``path`` with the platform's audio player; warn (never fail) when none works.

    A missing player is not a failed command: the bytes are on disk and the caller was told
    where. Exiting non-zero here would also throw away the file the user just paid to fetch.
    """
    import shutil
    import subprocess
    import sys

    from onepin._cli.render import echo_warning

    if sys.platform == "darwin":
        candidates = [["afplay"], ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]]
    elif sys.platform == "win32":
        # ffplay first: the samples default to .mp3 and `Media.SoundPlayer` loads WAV only.
        # The path is bound through `param($p)` rather than appended to the command text —
        # `powershell -Command "<text>"` parses trailing argv as *more command text* and
        # never populates `$args`, so appending it both fails to play and makes any `;` or
        # `$(...)` in the caller's --out path execute as PowerShell.
        candidates = [
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"],
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "param($p) (New-Object Media.SoundPlayer $p).PlaySync()",
            ],
        ]
    else:
        candidates = [["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"], ["aplay"], ["mpg123", "-q"]]

    last_error: Optional[str] = None
    for command in candidates:
        if shutil.which(command[0]) is None:
            continue
        try:
            subprocess.run([*command, str(path)], check=True)
        except (subprocess.CalledProcessError, OSError) as exc:
            # Keep going: the list is ordered by preference, not by what can decode this
            # file. `aplay` handles WAV only, so an .mp3 has to reach `mpg123` behind it —
            # returning here would report "cannot play" on a machine that can.
            last_error = str(exc)
            continue
        return
    if last_error is not None:
        echo_warning(f"Could not play {path}: {last_error}")
    elif not json_on:
        echo_warning(f"No audio player found; the sample is at {path}.")


def _sample_label(row: dict[str, Any]) -> str:
    """Name / locale for one row, carrying the locale substitution when there was one."""
    locale = row.get("locale") or "unknown locale"
    label = f"{row.get('name') or row['voice_id']} ({locale})"
    if row.get("fallback"):
        # The caller asked for a locale they did not get; saying so is the whole point, and it
        # has to be said before the clip plays rather than after it is already misheard.
        label += " — no preview in the requested locale, using its default sample"
    return label


def _emit_samples(rows: list[dict[str, Any]], json_on: bool) -> None:
    if json_on:
        render_json(rows)
        return
    for row in rows:
        label = _sample_label(row)
        if row.get("path"):
            typer.echo(f"Wrote {label}: {row['path']}")
        else:
            typer.echo(f"{label}: {row['sample_url']}")


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


def _run_scoped_body(script: Optional[str], source_language: Optional[str]) -> Optional[dict[str, Any]]:
    """Build ``request_options`` carrying the run-scoped overrides, or ``None`` for neither.

    ``workflows run`` and ``workflows preview-run`` share this so an estimate prices the exact
    body the run will send — two builders could drift, and a cost quoted from a different body
    than the one charged is precisely the failure these overrides exist to prevent.

    Sent as additional body parameters rather than a ``WorkflowRunStartIn``: the generated model
    defaults both fields to ``None``, so Fern serializes the unset one as an explicit
    ``"source_language": null`` instead of omitting it. Building the dict keeps only the keys the
    user actually passed, which is the wire format this endpoint has always been called with.
    """
    overrides = {
        key: value
        for key, value in (("script_text", script), ("source_language", source_language))
        if value is not None
    }
    return {"additional_body_parameters": overrides} if overrides else None


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
