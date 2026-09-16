---
name: onepin
description: >-
  Use when the user mentions Onepin or wants to operate a Onepin voice-workflow
  workspace from the terminal — list / inspect / build / run workflows, check run
  status, audition voices, hand back the generated audio, browse templates, inspect
  usage. Onepin is an AI voice-workflow platform with a `onepin` CLI; this skill
  drives it safely and makes sure the user actually hears the result.
---

# Onepin

Drive a Onepin voice-workflow workspace through the `onepin` CLI. The CLI is the only
integration surface — this skill teaches its contract, not a frozen command list.

## What this product is

Onepin turns scripts into speech. A workflow is a graph of nodes that normalizes text,
synthesizes audio, translates, and validates the result; runs are asynchronous — start one,
then poll it. Three rules follow from that and they outrank the mechanics below:

- **The deliverable is audio — never answer about it in text alone.** Every `sample_url` /
  `language_sample_url` / `playback_url` the CLI returns is a plain audio file on an ordinary
  presigned URL (no auth header, good for about an hour). Play it, or hand it over as a titled
  markdown link — never a bare URL. See *Audio: the part you must not skip*.
- **Never start audio unannounced.** Say whose voice or which line you are about to play, or
  list the options and ask which one they want to hear. Sound arriving with no warning —
  especially at the end of a long run the user stopped watching — is startling.
- **Reuse before you build, and make it the user's choice.** Before authoring a workflow, look
  at what the workspace already has and offer *both* paths. See *Reuse before you build*.

## The flow

"Make me some speech" is not one command — it is a short conversation with decisions that belong to
the user, not to you. Walk it in order and stop at each question.

1. **Which workflow?** `onepin --json workflows list` *and* `templates list`. Put the existing
   workflows (named with their languages and voices), the gallery templates, and **"build a new
   one"** into a single question. → *Reuse before you build*
2. **Show it before it costs anything.** `workflows show <workflow_id>` → render the pipeline, the
   voice per language, and the quality gates. → *Show the workflow before you run it*
3. **The voice — keep it, hear it, or change it?** Ask; don't assume the saved one is wanted.
   - *hear it*: `voices list --language <locale> --search <name>` → announce → play
     `language_sample_url`. → *Audio: the part you must not skip*
   - *change it*: there is **no set-voice command**. Patch the generator's
     `config.voice_map["<locale>"]` in the definition and `workflows update <id> --definition @wf.json`
     (a `VoiceAssignment` needs at least `voice_id`, `provider`, `model`).
4. **The script.** Their exact text on `workflows run --script`, with `--source-language` when it
   isn't the saved one. → *The script is the user's*
5. **Price, then permission.** `workflows preview-run <workflow_id>` → show the expected credits →
   get an explicit yes → `workflows run`. Poll `runs status`, or run with `--watch --timeout 300`.
6. **Hand over the audio.** `runs data` → announce → play or link every line. A run that finished
   and was only described in text is not finished. → *Audio: the part you must not skip*

**If they chose to build a new one**, step 2 becomes its own set of questions — ask, don't pick for
them, and confirm every slug against `nodes list` first:

- **Source** — `source_script` (their text or an upload).
- **Operators** — a `operator_normalizer` (numbers, dates, abbreviations → spoken form)? an
  `operator_translator` (`target_languages`) if they want other languages? an
  `operator_phoneme_injector` if pronunciation matters?
- **Generator** — `operator_generator`, one `voice_map` entry per locale.
- **Validators** — which checks, and at what bar: word accuracy, naturalness, clarity,
  pronunciation. Each has a `threshold` and `max_retries`; the defaults are not all the same and are
  listed in [reference.md](reference.md).
- **Sink** — `sink_preview` (`format`: `wav` or `mp3`).

Then `workflows definition-schema` → `workflows create --definition @wf.json` → and you are back at
step 3. There is no separate validate command: `create` is what rejects an invalid graph.

## Golden rules

- **Discover, don't guess.** `onepin schema` prints a JSON manifest of every command
  (`path`, `args`, `options`, and a `destructive` flag). Look a command up before building
  it; never invent flags from memory.
- **Put `--json` immediately after `onepin`** — e.g. `onepin --json workflows list`. This global
  position works for *every* command; a trailing `--json` (e.g. `onepin whoami --json`) fails on
  some commands. Parse **stdout** as JSON.
- **The exit code is the success signal, not stdout.** With `--json`, success prints the JSON
  payload to **stdout**; a failure prints a `{"error": {"code": "...", "message": "..."}}` envelope
  to **stderr** and exits non-zero. So: exit `0` → parse stdout; non-zero exit → read the error
  envelope from stderr. Don't expect an `error` key on stdout (on failure stdout is empty).
- **Exit codes:** `0` ok · `1` API/runtime error · `2` usage error · `130` interrupted.
- **Never run a destructive command without explicit confirmation** (see below). Don't add
  `--yes` to silence a prompt.

## Preflight (do this first, once)

1. `onepin --version` — if "command not found", tell the user to `pip install onepin`, then stop.
2. `onepin --json whoami` — confirms authentication. On success note `workspace_id`, `scopes`.
   - Unauthenticated (`NOT_LOGGED_IN` / `INVALID_API_KEY`) → tell the user to run `onepin login`
     (mint a key at https://app.onepin.ai/workspace/~/settings/api), then stop.
   - Pass `--workspace <uuid>` (or set `ONEPIN_WORKSPACE_ID`) only if the user has more than one
     workspace and the wrong one is active.
3. If `onepin schema` errors or the command is missing, the CLI is old — suggest
   `pip install -U onepin`, or fall back to `onepin <group> --help`.
4. **Offer upgrades (advisory, never block the task).** Run `onepin upgrade-check` (it prints
   nothing when up to date, snoozed, offline, or disabled via `ONEPIN_NO_UPDATE_CHECK`).
   - On `UPGRADE_AVAILABLE <current> <latest>`: ask with AskUserQuestion — **Upgrade now**
     (run `onepin upgrade-check --mark-upgrading && pip install --upgrade onepin` — the marker lets
     the next run confirm the new version), **Not now** (run `onepin upgrade-check --snooze` — an
     escalating quiet period: 24h, then 48h, then 7d), or **Don't ask again** (run
     `onepin upgrade-check --disable`). Continue with the task either way.
   - On `JUST_UPGRADED <old> <new>`: tell the user they're now on v`<new>` and continue.
   Separately, if *any* command fails with `UPGRADE_REQUIRED` (or an HTTP 426), the SDK is too old to
   talk to the API — surface the message and its `pip install --upgrade` command, and stop.

## Discover, don't guess

`onepin schema` → `{name, version, commands: [{path, args, options:[{flag,type,required,default,help}], destructive}]}`.
Look up the exact command before building it. `destructive: true` ⇒ it has `--yes` ⇒ apply the
confirmation rule below.

## Core flows

Lead every command with `--json` (`onepin --json <command> …`); summarize results for the user
rather than dumping raw JSON. Two things are *not* summaries: the audio (play it or link it —
see below) and the workflow you are about to run (show its shape before it costs anything).

### Workflows
- List: `onepin --json workflows list` — filters `--status`, `--search`, `--sort`, `--order`,
  `--limit`. **Lists are paginated and truncated:** default `--limit` is 50, the max page is ~100
  (larger values return `422 VALIDATION_ERROR`), and most list commands take no offset/cursor — so a
  large set cannot be fully enumerated. Narrow with `--search`/filters; if results are capped, tell
  the user the list is partial rather than implying it is complete. (The two commands that *can* be
  paged through: `workflows runs data --offset` and `usage activity --cursor`.)
- Inspect: `onepin --json workflows show <workflow_id>`
- Estimate cost before running: `onepin --json workflows preview-run <workflow_id>`
- **Run (starts a real, billable execution):** `onepin --json workflows run <workflow_id>`. A run
  consumes credits and acts on the live workspace. It is *not* `--yes`-gated, so for an expensive,
  production, or ambiguous run, confirm with the user first (and consider `preview-run`).
- Run and wait: `onepin --json workflows run <workflow_id> --watch --timeout 300` — polls to a
  terminal state (`completed`/`failed`/`cancelled`) and returns the final status inline (no
  separate status call). Exit is non-zero if the run failed or timed out.
- **Run one-off text without editing the workflow:** `--script "<text>"` overrides the saved script
  for that run only; add `--source-language <bcp-47>` (e.g. `en-us`) when the text isn't in the
  workflow's saved language. The workflow itself is left untouched.
- **Build/design a workflow:** check *Reuse before you build* first — then see the node catalog
  (slugs, ports, plan gating) and the *Designing a workflow* topology rules (sources → processing → generators → validators →
  sinks; validator pass/fail pins and retries) in [reference.md](reference.md). Discover slugs with
  `onepin nodes list` — never invent them.

### Runs
- List / inspect: `onepin --json workflows runs list <workflow_id>` ·
  `runs show <workflow_id> <run_id>` (the full record) · `runs status <workflow_id> <run_id>` (just
  the state — the one to poll).
- **Diagnose a run** (why it failed, what each node did): `runs overview <workflow_id> <run_id>` for
  the per-node rollup, then `runs steps <workflow_id> <run_id>` for the individual steps. Step
  results are **lightweight by default** — pass `--include-result` for full result payloads, and
  narrow with `--node-type <type>` / `--node-id <id>` (combinable) instead of pulling everything.
- Output rows: `onepin --json workflows runs data <workflow_id> <run_id>` — `--search`, `--language`,
  and, unusually for this CLI, real paging via `--limit` / `--offset`.
- Stats over a window: `onepin --json workflows runs summary <workflow_id> --from <iso> --to <iso>`.
- Download outputs to a file: `onepin workflows runs download <workflow_id> <run_id> --out export.zip`
  (atomic; refuses to overwrite without `--force`). For a single node's output:
  `onepin workflows runs download-node <workflow_id> <run_id> <node_id> --out <path>`.

### Voices
- `onepin --json voices list` — filters `--provider`, `--gender`, `--language`, `--search`.
  `--language` accepts only specific comma-separated codes (e.g. `en-us`, `en-gb`, `en`); an
  unsupported code returns `422` — don't guess regions, and note a voice's own
  `supported_languages` may be broader than the filter codes. Same pagination cap as above
  (default 50, ~100 max, no offset), so the full catalog can't be listed in one call.
- `onepin --json voices show <voice_id>` · `onepin --json voices similar <voice_id>` ·
  `voices favorite` / `unfavorite <voice_id>` (and `voices list --favorites-only`).
- **Voices are chosen by ear.** Don't stop at the names — see *Audio: the part you must not skip*
  for which sample URL to play and how to announce it.

### Templates
- `onepin --json templates list` — filters `--category`, `--sort`, `--search`
- `onepin --json templates show <template_id>`

## Audio: the part you must not skip

The user paid credits for sound. A reply that lists voice names, or reports "the run completed",
and never puts audio in front of them has not delivered the thing they asked for.

**Hearing a voice.** `onepin --json voices list --language <code> --search <name>` — each row's
`language_sample_url` is the clip *in the language you filtered for*, and `language_sample_locale`
is the region it actually came from: report that, not the code you asked for (a bare family like
`en` expands to `en-us` or `en-gb`, and only that field says which one they heard). A row's plain
`sample_url` — also on `voices show <voice_id>` — is playable but does **not** follow `--language`,
so it may be the wrong language; use it only as a fallback when `language_sample_url` is null.
List the shortlist with names first and ask which one they want to hear, then play that row.

**Hearing a run.** `onepin --json workflows runs data <workflow_id> <run_id>` → `rows[].cards[]`,
one card per line per locale, each carrying `script`, `locale_code`, `voice`, `validations[]`,
`retry_count` and `audio.playback_url` (plus `audio.status`, `duration_ms`, `provider`, `model`).
That is the per-line audio. A card whose `audio.status` is not ready carries no `playback_url` —
say so instead of reporting that line as delivered, and the same for `dropped` / `rejected` cards.
If you narrowed with `--limit` / `--offset`, tell the user the page is partial. For files on disk
instead of URLs: `runs download` (whole run) or `runs download-node` (one node).

**Playing it.** Every one of these URLs is a plain audio file with no auth header, valid for about
an hour — re-run the command to re-sign rather than caching it.

```bash
curl -fsSL "<url>" -o /tmp/onepin-clip.mp3 && afplay /tmp/onepin-clip.mp3   # macOS
ffplay -nodisp -autoexit "<url>"                                           # takes the URL directly
# Windows: start "<url>" · Linux without ffplay: xdg-open "<url>"
```

`afplay` takes a *file*, not a URL — hence the `curl` — and it **blocks for the clip's whole
duration**, so it is for samples and single lines, never a whole export (that is what
`runs download` is for). Three things this cannot tell you:

- **Exit `0` does not mean they heard it.** The player returns success whether the output device is
  headphones, a muted monitor, or something else entirely. Say what you just played, and offer the
  link if they say they heard nothing.
- **There may be no audio device at all.** If your shell is not on the user's own machine — SSH, a
  container, CI, a cloud session — playing is not an option; go straight to the links below.
- **Playing makes noise on someone's desk.** That is why the announcement rule above is not
  optional.

Announce it first — whose voice, or which line. **If you cannot play sound**, hand over one titled
markdown link per clip, each on its own line:

- `[▶ Line <line_index>](<playback_url>)` — use the response's own `line_index`, never the script
  text, which can contain brackets that close the link early and send the click elsewhere.
- `[▶ <voice name> (<locale>)](<language_sample_url>)` — dropping any brackets or parentheses from
  the name, for the same reason.

**Never paste the bare URL.** It is a presigned link hundreds of characters long, and the title is
how the user knows whose voice, or which line, they are about to open.

## The script is the user's

Whatever reaches a run is the user's bytes: pass their exact text to `workflows run --script`, from
the message or file they gave you. Do not quietly normalize, re-punctuate, translate, or "clean up"
a script on the way in — TTS output changes audibly when the text does. If a change would help
(expanding numerals, fixing an obvious typo), show the rewrite and get agreement first, then run it
as its own `--script`. `--source-language` is BCP-47 and a bare family resolves to a region, so
report the region that was actually used rather than the code you passed.

## Reuse before you build

`workflows create` is reachable without ever looking at what the workspace already has — which is
how a user ends up with a fifth Korean-dub workflow beside four that already did the job. So before
authoring anything:

1. `onepin --json workflows list` and `onepin --json templates list` (`--search` to narrow).
2. **Offer both paths in one question.** Name each candidate with its languages and voices, and put
   "build a new one" alongside them as a choice — not as something the user has to know to ask for.
   Reuse beats authoring when something already does the job, but *which it is is the user's call.*
3. If they pick an existing workflow → `workflows show` it (see below), then `preview-run`.
   If they want something new → clone from the gallery first (`templates clone <template_id>`);
   cloning is faster and cannot produce an invalid graph. Author from scratch with
   `nodes list` / `nodes show` only when nothing in the gallery fits.

**What counts as "already exists" is narrow and exact:** the same (normalized) name, or an identical
language set *and* an identical multiset of node types. Nothing fuzzy. A near-miss reported as a
duplicate is worse than no check at all — it teaches the user to wave the question away.

**A check that could not run is not a check that found nothing.** Scopes are flat here: a
write-only key gets `FORBIDDEN` on the very list this reads. If the list call fails, say the reuse
check couldn't run — never "nothing similar exists".

## Show the workflow before you run it

A run costs credits and acts on the live workspace, so the user has to be able to see what they are
agreeing to. `workflows show <workflow_id>` returns the definition as JSON — turn it into something
readable *before* asking, and lead with the parts they can actually judge:

- the **pipeline** in order (source → processing → generator(s) → validator(s) → sink),
- the **voice per language** (the most audible decision the graph makes),
- the **quality gates**: which validators, their thresholds, and the max-retry guard.

Then `preview-run` for the cost, get an explicit yes, and only then `run`. If several workflows could
plausibly be the one they meant, list the others with their languages and voices too.

## Destructive operations (require explicit confirmation)

`workflows delete`, `templates delete`, `uploads delete`, `workspace delete`,
`workflows runs cancel`, `workspace members remove`,
`workspace members revoke-invite` — all irreversible — plus `skill uninstall`, which only removes
this skill's local files and can be undone with `onepin skill install`. Procedure:

1. **Resolve the exact target.** Confirm the id/name actually exists (via `--search` or a `show`);
   never act on a fuzzy match — `"test"` is not `"test-tts"`.
2. **Get an explicit yes.** State plainly what will be deleted/cancelled and that it cannot be undone.
3. **Then run with `--yes`** (e.g. `onepin --json workflows delete <id> --yes`). Without `--yes` the
   CLI emits an interactive prompt that can hang in a non-interactive shell, so confirm with the
   user first, then pass `--yes`. A `CONFIRMATION_REQUIRED` error means "stop and ask" — never
   "retry with `--yes`."

## Output & errors

- On exit `0`, parse stdout as JSON. On any non-zero exit, read the error envelope from **stderr**
  — `{"error":{"code":"NOT_FOUND","message":"..."}}` (also `VALIDATION_ERROR`, `FORBIDDEN`,
  `RATE_LIMITED`, `NOT_LOGGED_IN`, `CONFIRMATION_REQUIRED`).
- Report failures to the user as `code: message`, plainly.

For the full command catalog and recipes (workflow definitions, uploads, workspace + members,
usage, nodes), see [reference.md](reference.md) or run `onepin schema`.
