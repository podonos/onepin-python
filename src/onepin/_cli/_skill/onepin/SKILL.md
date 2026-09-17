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

- **The deliverable is audio — play it out loud.** Every `sample_url` / `language_sample_url` /
  `playback_url` the CLI returns is a plain audio file on an ordinary presigned URL (no auth
  header, good for about an hour). **Playing is the default, not one of two equal options**:
  `--play` and `afplay` are already in your hands, so a reply that hands over links while sitting
  at a terminal that can make noise has made the user do the last step themselves. A titled
  markdown link is the *fallback* for a shell with no speakers — and a bare URL is never either.
  See *Audio: the part you must not skip*.
- **Announce, then play — don't ask for permission to play.** Say whose voice or which line is
  coming, then play it in the same turn; sound arriving with no warning — especially at the end of
  a long run the user stopped watching — is startling. "Announce" means one line naming what is
  about to be heard, not a question. Stopping at *"here are the samples, have a listen and tell me
  which"* is the failure this rule exists to prevent: you were holding the audio and handed back
  homework. Ask first only when playing is itself the imposition — a long export, or audio they did
  not ask for.
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
   - *hear it*: `voices list --language <locale> --search <name>` to build the shortlist, then
     announce it and `voices sample <id>... --language <locale> --play` — **every** candidate in
     one call, not just the one whose name you liked. The shortlist and the audio go out in the
     same turn: name them 1..N, play them 1..N, ask for a number.
     → *Audio: the part you must not skip*
   - *change it*: ask what they want it to sound like, then hand that description to the server —
     `voices list --language <locale> --search "<their words>"` comes back ranked and already
     narrowed. → *Let the server pick the shortlist*. Then stop: `workflows set-voice` is one
     command, but a voice change is **not** run-scoped — it rewrites the saved workflow, and it
     needs a yes of its own before you touch anything. → *Changing a voice is not run-scoped*
4. **The script.** Their exact text on `workflows run --script`, with `--source-language` when it
   isn't the saved one. → *The script is the user's*
5. **Price, then permission.** `workflows preview-run <workflow_id>` **with the same
   `--script`/`--source-language` you are about to run** → show the expected credits → get an
   explicit yes → `workflows run`. Poll `runs status`, or run with `--watch --timeout 300`.
   Every run, however small; if `preview-run` fails, make it work — never turn the script's length
   into a credit figure. → *Running a workflow*
6. **Hand over the audio.** `runs data` → announce → play every line (link it only when this shell
   cannot play). A run that finished and was only described in text is not finished.
   → *Audio: the part you must not skip*

**If they chose to build a new one**, step 2 becomes its own set of questions — ask, don't pick for
them, lead with a recommendation rather than a menu, and confirm every slug against `nodes list`
first. → *Designing a new workflow*

- **Source** — `source_script` (their text or an upload).
- **Operators** — a `operator_normalizer` (numbers, dates, abbreviations → spoken form)? an
  `operator_translator` (`target_languages`) if they want other languages? an
  `operator_phoneme_injector` if pronunciation matters?
- **Generator** — `operator_generator`, one `voice_map` entry per locale. Build each entry from a
  `voices list` row (`voice_id` is the row's `provider_voice_id`, not its `id` — see reference.md).
- **Validators** — which checks, and at what bar: word accuracy, naturalness, clarity,
  pronunciation. Each has a `threshold` and `max_retries`, and **the defaults differ per validator**
  — read the real one out of `nodes list` (`.config_schema.threshold.default`) and quote that number
  to the user instead of saying "the default". **Leaving validators out is itself a decision**, and
  one only the user gets to make. → *Designing a new workflow*
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
- **Never start a run without explicit confirmation.** `workflows run` spends the user's credits and
  is *not* `--yes`-gated, so nothing stops you but the procedure in *Running a workflow*. There is no
  cheap-enough, small-enough or obvious-enough exemption — ask every time.

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
  `--limit`, `--offset`. **One page is not the result set:** default `--limit` is 50 and the max page
  is ~100 (larger values return `422 VALIDATION_ERROR`), so walk a bigger set by stepping `--offset`
  **by the `--limit` you passed** — `--limit 100 --offset 100`, `--limit 100 --offset 200`, … A
  stride wider than the page silently skips the rows in between. Without `--json` the footer prints
  `Showing X of N` — `N` is how many *matched*, so it is the number that tells you whether you are
  holding all of them; it already accounts for `--offset`, so page until it says no more. Filters
  still beat paging: narrow with `--search` first and page only when the user genuinely wants the
  whole set.
- Inspect: `onepin --json workflows show <workflow_id>`
- Estimate cost before running: `onepin --json workflows preview-run <workflow_id>` — takes the
  same `--script` / `--source-language` as `run`, and pass them whenever the run will, because the
  estimate prices the body it is given, not the one you intend to send. No run, no credits.
- **Run (starts a real, billable execution):** `onepin --json workflows run <workflow_id>`. A run
  consumes credits and acts on the live workspace. It is *not* `--yes`-gated — confirm with the user
  first, every time, by the procedure in *Running a workflow*.
- Run and wait: `onepin --json workflows run <workflow_id> --watch --timeout 300` — polls to a
  terminal state (`completed`/`failed`/`cancelled`) and returns the final status inline (no
  separate status call). Exit is non-zero if the run failed or timed out.
- **Run one-off text without editing the workflow:** `--script "<text>"` overrides the saved script
  for that run only; add `--source-language <bcp-47>` (e.g. `en-us`) when the text isn't in the
  workflow's saved language. The workflow itself is left untouched.
- **Build/design a workflow:** check *Reuse before you build* first — then ask the catalog
  (`nodes list` — slugs, ports, config keys, plan gating) and read the *Designing a workflow*
  topology rules (sources → processing → generators → validators →
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
- `onepin --json voices list` — every filter is applied **server-side**: `--search`, `--language`,
  `--gender`, `--age`, `--category`, `--accent`, `--source`, `--provider`, `--model`,
  `--favorites-only`, plus `--sort`/`--order`. Filters AND across fields; a comma-separated value
  ORs within one. Ask the server for the shortlist instead of paging the catalog →
  *Let the server pick the shortlist*.
- **`onepin --json voices facets` answers "what can I filter by, and how much is left?"** — one call
  returns every provider, model, language, gender, age, category and accent that exists, each with
  a match count, and it takes the same filters so the counts narrow as you add them. Its `value`s
  are exactly what `voices list` accepts, so use it instead of guessing a locale code into a `422`
  or offering the user a filter that would return nothing.
- `--language` accepts only specific comma-separated codes (e.g. `en-us`, `en-gb`, `en`); an
  unsupported code returns `422` — don't guess regions, and note a voice's own
  `supported_languages` may be broader than the filter codes.
- Same paging as above (`--limit` default 50, ~100 max, `--offset` stepped by that same `--limit`
  to walk) — but a voice catalog
  is one of the sets you should *not* walk by hand: an unfiltered page is an arbitrary slice, and
  the point of the filters is to make the first page the right one.
- `onepin --json voices show <voice_id>` · `onepin --json voices similar <voice_id>` ·
  `voices favorite` / `unfavorite <voice_id>` (and `voices list --favorites-only`).
- **Audition them:** `onepin voices sample <voice_id>... --language <locale> --play` takes as many
  ids as you have candidates, mints a fresh sample URL for each, and plays them in order, naming
  each voice just before its clip. `--play` is the normal form; `--out-dir <dir>` writes files
  instead, and passing neither prints name / locale / model / URL to hand over when there is no way
  to play. Sample URLs expire after about an hour — re-run the command to re-sign rather than
  reusing an old link.
- **Voices are chosen by ear.** Don't stop at the names — see *Audio: the part you must not skip*
  for which sample URL to play and how to announce it.

### Templates
- `onepin --json templates list` — filters `--category`, `--sort`, `--search`
- `onepin --json templates show <template_id>`

## Let the server pick the shortlist

A voice catalog is far bigger than one page — `voices list` returns at most ~100 rows, and one
locale can hold several pages of them. `--offset` will walk the whole thing, but reading a few
hundred rows of near-identical tags is not how anyone picks a voice, and whatever you pick off an
arbitrary page was not really chosen. The fix is not to page harder: **every filter on
`voices list` runs server-side, so state the requirement and let the server hand back the
shortlist.**

1. **Describe the voice — `--search` takes words, not just names.** The server matches the query
   against a voice's meaning as well as its name, tags and descriptor, and returns one
   relevance-ranked list, so the user's own phrasing *is* the query:
   `--search "warm, unhurried documentary narrator"` surfaces calm, measured voices that share no
   literal word with it. Pass what the user said.
2. **Pin every axis you actually know — there is a flag for each.** `--language <locale>` (which
   also fills `language_sample_url` on every row, so the shortlist is auditionable without a call
   per voice), `--gender`, `--age`, `--category` (the delivery style: `narration`, `podcast`,
   `news`, …), `--accent`, `--source` (`platform` vs. this workspace's own), `--provider`,
   `--model`, and `--favorites-only` for what this workspace already liked. Don't pull rows you
   could have excluded in the request.
3. **Ask `voices facets` when you don't know what to ask for.** It reports the values that exist
   with a count each, under the filters you already have — so "is there even a Korean
   conversational voice?" is one call, not a search that comes back empty and tells you nothing.
   Reach for it before guessing a value, and after an empty result to see which axis emptied it.
4. **Refine on the returned rows only for what has no flag**, and say that you did: `tags`,
   `description`, `uses_count`. Anything with a flag belongs in the request instead. And a
   row-level refinement is never a catalog-wide answer — it only sorted the page you were handed.
5. **"More like that one" is also a server call.** `voices similar <voice_id> --language <locale>`
   when the user liked a voice but not quite — better than re-listing and re-reading names.

**Empty means widen, not enumerate.** A `--search` plus three filters can legitimately match
nothing. Relax `--search` first (it is the fuzziest constraint), then one filter at a time, and tell
the user what you dropped — or run `voices facets` with the same filters to see which axis is the
one at zero. The wrong recovery is an unfiltered `voices list` read by eye.

**Read the count, and check the row is usable.** The row count is bounded by `--limit` and is never
"how many matched" — the match count is the `N` in the `Showing X of N` footer (text output; under
`--json` you get the rows alone, so page to find the end). And a row can be listed but unusable:
check `is_active` / `availability` before offering a voice, and check that the `model` you mean to
wire appears in its `model_capabilities[]` *for that locale*.

Then hand the shortlist over by ear, not by name.

## Audio: the part you must not skip

The user paid credits for sound. A reply that lists voice names, or reports "the run completed",
and never puts audio in front of them has not delivered the thing they asked for.

**Hearing a voice.** Have the server narrow it first (*Let the server pick the shortlist*), then
audition what comes back. `onepin --json voices list --language <code> --search "<what they asked
for>"` — each row's
`language_sample_url` is the clip *in the language you filtered for*, and `language_sample_locale`
is the region it actually came from: report that, not the code you asked for (a bare family like
`en` expands to `en-us` or `en-gb`, and only that field says which one they heard). A row's plain
`sample_url` — also on `voices show <voice_id>` — is playable but does **not** follow `--language`,
so it may be the wrong language; use it only as a fallback when `language_sample_url` is null.

**Tags are a filter, not an audition.** `bright`, `clear`, `friendly` are how you *got* the
shortlist; they are not how anyone picks a voice. One locale can carry dozens of voices whose tags
are near-identical — a user reading that list is choosing adjectives, not sound. Hand over the whole
shortlist by ear instead, in one call:

```bash
onepin voices sample <id-1> <id-2> <id-3> --language ko-kr --play   # the default: announce, then play
onepin voices sample <id-1> <id-2> <id-3> --language ko-kr          # name / locale / model / URL
```

**`--play` is the first form for a reason.** It fetches, writes and plays in order, naming each
voice on its own line *before* that clip starts, so a shortlist played in one call is still
followable by ear. Announce the list in your own reply too — same numbering as the command's
argument order — and then let it run. The bare second form is for a shell that cannot play: it
prints one row per candidate to turn into titled links.

Asking *"which of these names do you want?"* while holding all of their samples turns a decision the
user could have made in thirty seconds into a guess. So does *"I've downloaded them, have a
listen"* — the fetch is not the deliverable, the sound is, and `--play` is one flag away.

**Report the locale you were served, not the one you asked for.** `voices sample` prints it per row,
and says so explicitly when a voice had no preview in the locale you requested and it fell back to
that voice's default sample — which may be another language entirely. Pass that on; a user
comparing Korean voices needs to know when one of them spoke English.

**Hearing a run.** `onepin --json workflows runs data <workflow_id> <run_id>` → `rows[].cards[]`,
one card per line per locale, each carrying `script`, `locale_code`, `voice`, `validations[]`,
`retry_count` and `audio.playback_url` (plus `audio.status`, `duration_ms`, `provider`, `model`).
That is the per-line audio. A card whose `audio.status` is not ready carries no `playback_url` —
say so instead of reporting that line as delivered, and the same for `dropped` / `rejected` cards.
If you narrowed with `--limit` / `--offset`, tell the user the page is partial. For files on disk
instead of URLs: `runs download` (whole run) or `runs download-node` (one node).

**Playing it.** For voices, `voices sample <id>... --play` does the whole thing — fetch, write,
play, in the right order for the platform. For a run's lines you still hold a URL, and every one of
these URLs is a plain audio file with no auth header valid for about an hour — re-run the command to
re-sign rather than caching it.

Whether this shell can make noise is a question with an answer — settle it once, up front, instead
of assuming it cannot and reaching for links:

```bash
[ -n "$SSH_TTY$SSH_CONNECTION" ] && echo "remote shell — link instead"
command -v afplay || command -v ffplay || command -v mpg123 || echo "no player — link instead"
```

A player on a local shell means **play**. Neither line is a reason to ask the user's permission
first; they are the only reasons to fall back to links.

```bash
curl -fsSL "<url>" -o /tmp/onepin-clip.mp3 && afplay /tmp/onepin-clip.mp3   # macOS
ffplay -nodisp -autoexit "<url>"                                           # takes the URL directly
# Windows: start "<url>" · Linux without ffplay: xdg-open "<url>"
```

`afplay` takes a *file*, not a URL — hence the `curl` — and it **blocks for the clip's whole
duration**, so it is for samples and single lines, never a whole export (that is what
`runs download` is for). Three things playback cannot tell you:

- **Exit `0` does not mean they heard it.** The player returns success whether the output device is
  headphones, a muted monitor, or something else entirely. Say what you just played, and offer the
  link if they say they heard nothing.
- **There may be no audio device at all.** If your shell is not on the user's own machine — SSH, a
  container, CI, a cloud session — playing is not an option; that is what the check above is for,
  and then you go straight to the links below.
- **Playing makes noise on someone's desk.** That is why the announcement rule above is not
  optional — but announcing is a sentence, not a request. Say what is coming and play it.

Announce it first — whose voice, or which line. **If the check above says you cannot play sound**,
hand over one titled markdown link per clip, each on its own line:

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

## Changing a voice is not run-scoped

`--script` and `--source-language` are the *only* run-scoped overrides `workflows run` has. There is
no `--voice` flag, so "use a different voice just for this one" — an entirely ordinary thing to want
— is not something the CLI can do. Every route to a new voice is an edit to the saved workflow:

- **`workflows set-voice <id> --locale <locale> --voice <catalog_voice_id>`** — the one to use. It
  moves a single `voice_map` entry, checks the voice can actually speak that locale and that the
  model covers it, and prints the assignment it replaced so you can put it back. Add `--node-id`
  when the graph has more than one generator; it refuses to guess rather than picking one.
- **`workflows update <id> --definition @wf.json`** — the whole-definition path. Only for changes
  `set-voice` cannot express, because it rewrites every node to move one field.
- **`workflows duplicate <id> --name "<name>"` first, then set the voice on the copy** — leaves the
  original exactly as it was, at the price of one more workflow in their list. Without `--name`
  every copy is called `<original> (Copy)`, indistinguishable a week later; name it for the change
  being made, and report the id you ended up on.

`set-voice` being one command does not make it a small change. It **overwrites the saved workflow
for every future run**, and the output says so on purpose.

Say which of the two you are proposing, and get a yes for it *before* the run gate and separately
from it — this is a permanent change to something the user built, not a run parameter. Never
describe a voice change as leaving the saved definition untouched. A user who is told their choice
applies to this run only, and whose workflow is then rewritten, agreed to a run and got an edit.

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

**Finding a match is not permission to use it.** A workflow whose name looks like what the user
asked for is a *candidate*. That distinction is the whole point: what you are about to adopt carries
a saved voice, a saved language set and saved quality gates the user has not seen yet. Put the three
real options to them — **reuse it as is**, **duplicate it and change the copy**, **build a new one**
— and stop on the question. Don't find it, inspect it and adopt it inside one turn: "there's already
a workflow for this, let me pull up its definition" reads as a progress report while it is in fact
the decision, taken without them.

**What counts as "already exists" is narrow and exact:** the same (normalized) name, or an identical
language set *and* an identical multiset of node types. Nothing fuzzy. A near-miss reported as a
duplicate is worse than no check at all — it teaches the user to wave the question away.

**A check that could not run is not a check that found nothing.** Scopes are flat here: a
write-only key gets `FORBIDDEN` on the very list this reads. If the list call fails, say the reuse
check couldn't run — never "nothing similar exists".

## Designing a new workflow (ask what goes in it)

"Build a new one" is not one decision, it is three — and `workflows create` will happily accept a
graph that skips all of them. `source → generator → sink` is a valid workflow, and it is also a
workflow with **no quality check at all**: whatever the model says on the first take is what ships,
and nothing in the run will ever report that it was wrong. Authoring that silently, because it is
the shortest definition to write, quietly drops the thing this product exists to do. So before
`create`, put the three questions below to the user with AskUserQuestion — **leading with a
recommendation**, not a menu: propose a shape, say why it fits their script, and let them cut it
down.

The ladder to recommend from (full topology rules, including fan-out and where a fail pin can
route: [reference.md](reference.md) → *Designing a workflow*):

| Shape | Graph | When |
|---|---|---|
| Minimal | `source → generator → sink` | one throwaway line, with the user told there is no check |
| + accuracy | `source → normalizer → generator → sink` | any script with numbers, dates, abbreviations |
| Higher accuracy | `source → normalizer → generator(s) → validator(s) → sink(s)` | **the default to propose** — anything the user will actually use |

1. **Validators — which checks, at what bar, and what a fail does.** The catalog covers word
   accuracy, naturalness, background noise and pronunciation; confirm the slugs with `nodes list`
   and never author one it did not return. Each carries a `threshold` and a `max_retries` guard,
   plus a fail pin that sends the line back for a regeneration — so quote both numbers in the
   question, not just the list of names. Thresholds commonly default to **85**, but **the defaults
   differ per validator**: read `.config_schema.threshold.default` out of `nodes list` and quote
   *that*. And say plainly what "none" buys: **with no validator the audio goes out unverified.**
   The user may well choose that for a one-off line — but it has to be their choice, said out loud,
   not the default you took for them because it was less to write.
2. **Operators — what happens to the text before it is spoken.** `operator_normalizer` (numbers,
   dates, abbreviations → spoken form), the pronunciation corrector for names and jargon, and
   `operator_translator` (`target_languages`) when they want more than one language. Ask against
   *their* script: `"1,200"`, `"Dr."` and a product name nobody pronounces right are the concrete
   reason to add one, and a script with none of them is a real reason to leave it out.
3. **Output — format, and where it lands.** `sink_preview` with `format` `wav` or `mp3` keeps the
   result in Onepin. If they want the files on their own disk, that is `runs download` after the
   run — not a different sink; say so rather than promising a local path the graph cannot produce.

Then `nodes list` for the slugs, `workflows definition-schema` for the wiring, and
`workflows create --definition @wf.json`. `create` is what rejects an invalid graph — there is no
separate validate command.

## Show the workflow before you run it

A run costs credits and acts on the live workspace, so the user has to be able to see what they are
agreeing to. `workflows show <workflow_id>` returns the definition as JSON — turn it into something
readable *before* asking, and lead with the parts they can actually judge:

- the **pipeline** in order (source → processing → generator(s) → validator(s) → sink),
- the **voice per language** (the most audible decision the graph makes),
- the **quality gates**: which validators, their thresholds, and the max-retry guard.

Then `preview-run` for the cost, get an explicit yes, and only then `run`. If several workflows could
plausibly be the one they meant, list the others with their languages and voices too.

## Running a workflow (spends credits — requires explicit confirmation)

`workflows run` is the one command that takes the user's money, and the CLI will not stop you: there
is no `--yes`, no prompt, no `CONFIRMATION_REQUIRED`. This procedure is the whole gate. It has no
exemption clause on purpose — "this one is cheap, I'll just go" is the judgement that turns a gate
into a formality, so it applies to every run: reruns, retries after a failure, and the second voice
of a comparison included.

1. **Resolve the exact target.** `workflows show <workflow_id>`, rendered — pipeline, voice per
   language, quality gates (see *Show the workflow before you run it*). If several workflows could
   plausibly be the one they meant, list the others with their languages and voices too.
2. **Price the exact run — and if pricing fails, fix the pricing rather than guess around it.**
   `onepin --json workflows preview-run <workflow_id> --script "<the text>"` gives `min_credits` /
   `expected_credits` / `max_credits` per node. **Pass every run-scoped override you are going to
   run with.** Priced without them it prices the saved definition, which is a different operation
   than the one being charged — and on a workflow whose script node is empty (the normal shape when
   the text arrives per-run) pricing without `--script` fails outright with `VALIDATION_ERROR`,
   because there is no text to count. When it fails, the job is to make `preview-run` work:
   - **`VALIDATION_ERROR` with no text to count** → pass `--script` (and `--source-language`). If
     the run's text genuinely has to live in the workflow — an upload-backed source — put it there
     (`uploads confirm --workflow-id`, or `workflows update --definition`) and price again. That is
     an edit to the saved workflow, so it needs its own yes before you make it.
   - **Anything else** → report the `code: message` and stop. No number means no run: a run you
     cannot price is one the user cannot agree to the cost of.

   **Never convert the script's length into credits.** Characters are not credits and no ratio
   between them holds: billing is per unit and the unit differs per node (character, UTF-8 byte,
   word), each locale adds its own, and a settled run carries a 1-credit floor. The platform's own
   pricing guide is quoted *per thousand* characters, so a per-character guess is off by roughly two
   orders of magnitude — and a confident wrong number is worse than no number, because it buys a yes
   for a cost the user never agreed to. A past run of the same workflow
   (`workflows runs list <workflow_id>` → `credits`) is worth quoting as context — "the last run of
   this cost N credits" — but it prices *that* script, not this one, and it is not a substitute for
   `preview-run`.

   **`token_cost` is not credits.** On a run record `token_cost` counts billing *units* — characters
   for the text nodes — so a run showing `token_cost: 107` can be a 1-credit run. The credit figures
   are `preview-run`'s `expected_credits`, the run record's own `credits` field (the actual debit),
   and the drop in `current_balance` between two estimates. Never quote `token_cost` as a cost.
3. **Ask — and put all four of these in the question.** A confirmation missing any of them does not
   count as a confirmation; it is a question the user has no way to answer:
   - **Which workflow** — name + `workflow_id`, and whether it already exists or you are about to
     create it.
   - **Which voice** — provider/model + voice name, whether that is the workflow's saved voice, and
     that they can hear it first (*The flow*, step 3). Wanting a different one is an edit to the
     workflow with its own yes, not a run parameter. → *Changing a voice is not run-scoped*
   - **How many credits** — the number `preview-run` gave you in step 2, not one you worked out.
     Not "a little", not "not much", not omitted. For multi-locale runs, say it is the total across
     locales.
   - **Whether the workflow itself changes** — `--script` / `--source-language` are run-scoped and
     leave the saved workflow untouched; they are the *only* run-scoped overrides there are.
     `workflows set-voice` / `workflows update --definition` edit it permanently. Say which of the
     two this is, and never claim the first one when you are doing the second.
4. **Get an explicit yes, then run.** `onepin --json workflows run <workflow_id>` (add
   `--watch --timeout 300` to poll to a terminal state).

**The gate is its own question — never bolted onto a parameter.** Settle the workflow, the voice
and the script first, each on its own, and let the last question be about nothing but the money.
"Which voice should I use? I'll start the run as soon as you pick" is not a run confirmation: the
user is still configuring, and you have quietly arranged for a configuration answer to double as
authorization to spend. The final question's options read *run it* / *don't run it*. Not a list of
voices, not a list of workflows, not a choice of format — those are all settled by then.

**A yes bought with a wrong fact is not a yes.** If any of the four turns out to be false after they
agreed — a different workflow than the one you named, a voice that was never the saved one, a cost
that moved, an edit you called run-scoped — the approval is void. Say what changed and ask again.
"They already said yes" does not carry over: they said yes to the other thing.

**Confusion is not consent, and it is not a waiver.** If the reply to your question is "what?",
"which one?", or plain irritation, that is a report that *the question* was unclear — nearly always
because it arrived without steps 1–3 behind it. The fix is to ask again, in one or two plain
sentences, with the four items filled in. The fix is never to drop the gate and run: dropping a
confirmation because confirming annoyed someone spends their credits on an answer they never gave.

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
