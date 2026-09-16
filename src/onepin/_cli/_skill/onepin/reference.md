# Onepin CLI reference

`onepin schema` (JSON manifest of every command: `path`, `args`, `options`, `destructive`) is the
**authoritative** source — when this file and `schema` disagree, trust `schema`. This file is a
durable map of the groups and the non-obvious recipes; it is not a per-flag mirror.

## `--json` placement

Put `--json` **immediately after `onepin`**: `onepin --json workflows list`. The global position
works for every command. A trailing `--json` works for the resource commands but **fails on the
hand-written ones** (`whoami`, `login`, `logout`) with "No such option" — so always use the global
position.

## Global flags (before the subcommand)

`--api-key` (env `ONEPIN_API_KEY`) · `--base-url` (env `ONEPIN_BASE_URL`) · `--workspace` (env
`ONEPIN_WORKSPACE_ID`) · `--json` · `--no-color` · `-v/--verbose` · `--debug` · `--version`.

## Command groups

| Group | What it covers |
|-------|----------------|
| `workflows` | CRUD + `run`, `preview-run`, `duplicate`, `definition-schema`, `uploads`; subgroup `runs` |
| `workflows runs` | `list`, `show`, `status`, `steps`, `overview`, `data`, `summary`, `cancel`, `download`, `download-node` |
| `templates` | `list`, `show`, `create`, `update`, `delete`, `clone`, `favorite`, `unfavorite` |
| `voices` | `list`, `show`, `similar`, `favorite`, `unfavorite` |
| `uploads` | `create` (presigned S3), `confirm`, `delete` |
| `workspace` | `list`, `show`, `create`, `update`, `delete`, `settings`; subgroup `members` |
| `workspace members` | `list`, `invite`, `set-role`, `remove`, `accept`, `invite-role`, `revoke-invite` |
| `usage` | `summary`, `by-language`, `activity` (`--range 30d/60d/90d`) |
| `nodes` | `list`, `show <node_type>` (workflow node types + runtime options) |
| `auth` | `login`, `logout`, `whoami` |
| `skill` | `install`, `path`, `uninstall` — manage this skill's own files (Claude Code, Cursor, Codex, Gemini, Copilot) |
| `schema` | the JSON manifest (the contract) |

## Destructive commands (need `--yes`; confirm with the user first)

`workflows delete` · `workflows runs cancel` · `templates delete` · `uploads delete` ·
`workspace delete` · `workspace members remove` · `workspace members revoke-invite` ·
`skill uninstall` (local files only — reversible with `skill install`).
Under `--json` without `--yes` they return `CONFIRMATION_REQUIRED` — that
means stop and ask, not retry. `templates unfavorite` / `voices unfavorite` are *not* destructive.

## Recipe: build a workflow definition

```bash
onepin --json nodes list                       # 1. discover node types
onepin --json nodes show <node_type>           # 2. inspect a node's ports/options
onepin workflows definition-schema             # 3. the JSON Schema a definition must satisfy
#    ...or copy a known-good definition from an existing workflow/template:
onepin --json workflows show <workflow_id>
onepin --json templates show <template_id>
onepin --json workflows create --name "My workflow" --definition @workflow.json   # 4. create
```

`--definition` accepts inline JSON or `@path/to/file.json`. Same flag on `workflows update`,
`templates create`, `templates update`.

**Check for an existing one before you author** (see *Reuse before you build* in SKILL.md). The
duplicate test is deliberately narrow and exact — the same normalized name, or an identical language
set *and* an identical node-type multiset — because a near-miss reported as a duplicate trains
everyone to ignore the check. Offer the candidates *and* "build a new one" as one question; the
choice is the user's. If `workflows list` / `templates list` fails (a write-only key gets
`FORBIDDEN`), report that the check could not run rather than that nothing similar exists.

## Node catalog

**`onepin nodes list` is authoritative and you can always call it** — that endpoint needs no API key
and no workspace header, so it works even before `login`. It returns, per node: the `node_type`
slug, `display_name`, `description`, `version`, `beta`, the `inputs`/`outputs` ports, and
`input_schema` / `config_schema`. `onepin nodes show <node_type>` adds `category` and `options` —
the runtime values you actually configure with (available target languages, provider/model choices,
a voice-picker link).

Read that output rather than this table. The labels, descriptions and the `beta` badge live in a
staff-editable catalog and are re-read per request, and **which nodes a workspace can use is
plan-gated** — a slug listed below that `nodes list` does not return is not available here. Never
author with a slug `nodes list` did not return.

What the table *is* good for: knowing which slug to look up, since the slug is the stable identity
and the display name is not. (Labels and descriptions below were read from the live catalog on
2026-09-16; treat them as a snapshot, not a contract.)

| `node_type` (stable) | Label today | Category | Ports | What it does |
|---|---|---|---|---|
| `source_script` | Script Input | source | 0 in / 1 out | Upload or type your script. |
| `operator_translator` | Translator | operator | 1 in / 1 out | Translate the script into one or more other languages. |
| `operator_normalizer` | Normalizer | operator | 1 in / 1 out | Rewrite each line the way it should be read aloud: numbers, dates, symbols, and abbreviations. |
| `operator_generator` | Voice Generator | operator | 1 in / 1 out | TTS engine - voice generation. **Auto-route** picks the model for the language/locale off Onepin's benchmark, balancing quality against price; or set provider + model by hand. Speed / emotion / tone are model-dependent. |
| `operator_phoneme_injector` | Phonemizer | operator | 1 in / 1 out | Work out how each word should be pronounced in context, so the Pronunciation Check knows what's correct. |
| `operator_pronunciation_corrector` | Pronunciation Corrector *(beta)* | operator | 1 in / 1 out | Automatically fix mispronounced words, keeping the same voice. |
| `sink_preview` | Export | output | 1 in / 0 out | Export final audio. Aggregates audio + scripts + validation results for download. |
| `validator_error_rate` | Word Accuracy | validation | 1 in / 2 out | Check the spoken audio matches the script, word for word. Pass / fail pins. |
| `validator_naturalness` | Naturalness check | validation | 1 in / 2 out | Rate how natural the generated speech sounds. Pass / fail pins. |
| `validator_noise` | Clarity check | validation | 1 in / 2 out | Check the audio is clean, with no background noise or artifacts. Pass / fail pins. |
| `validator_pronunciation` | Pronunciation check *(beta)* | validation | 1 in / 2 out | Check each word is pronounced correctly, sound by sound. Pass / fail pins. |

Every validator's threshold is **adjustable** — the defaults differ per validator, see *Node config
keys* below — and each carries a per-object **retry counter**: each visit increments it, and once it
reaches `max_retries` (3 by default) the object leaves through the **pass** pin regardless of score,
which is what stops a fail→regenerate loop from running forever.

Costs differ per node and the generator/translator price against the vendor you pick, so
`workflows preview-run` — not this table — is what tells the user what a graph will cost.

## Node config keys

What each node takes in its `config`, read from the live catalog on 2026-09-16 — `nodes list`
(`config_schema`, a bare name → schema map) is the source of truth, and `nodes show <node_type>`
adds the runtime option values (available languages, provider/model choices, a voice-picker link).

| `node_type` | `config` keys (defaults where set) |
|---|---|
| `source_script` | `input_type` (`text` / `file` / `media`), `text`, `upload_ids`, `csv_column`, `csv_has_header` = `true`, `source_language`, `input_mode` = `plain` (`plain` / `markup`) |
| `operator_translator` | `target_languages` |
| `operator_normalizer` | `engine` = `llm`, `target_locale` |
| `operator_generator` | `voice_map`, `target_locale` |
| `operator_phoneme_injector` | `max_ngram` = `1` [1–5], `llm_candidate_filter` = `true`, `exclude_address_rows` = `true`, `use_derived_word_parts` = `true` |
| `operator_pronunciation_corrector` | `n_candidates` = `2` [1–8], `seed`, `target_ipa_source` = `dictionary` (`dictionary` / `ped`), `fallback_to_detector_ipa` = `true` |
| `validator_error_rate` | `threshold` = `93.0` [70–99], `max_retries` = `3` [1–50] |
| `validator_naturalness` | `threshold` = `70.0` [0–100], `max_retries` = `3` [1–50] |
| `validator_noise` | `threshold` = `70.0` [0–100], `max_retries` = `3` [1–50] |
| `validator_pronunciation` | `threshold` = `99.0` [0–100], `max_retries` = `3` [1–50], `k` = `1.0` |
| `sink_preview` | `format` = `wav` (`wav` / `mp3`) |

Two things worth knowing before you propose a graph:

- **Validator defaults are not uniform.** Word accuracy sits at 93 (and is clamped to 70–99);
  naturalness and clarity at 70; pronunciation at 99. All four retry 3 times. Say the number you are
  proposing rather than "the default".
- **A voice lives in `operator_generator.config.voice_map`** — a map of locale → list of
  `VoiceAssignment`, each needing at least `voice_id`, `provider` and `model` (optionally
  `catalog_voice_id`, `voice_name`, `provider_config`, `canonical_controls`). Changing a workflow's
  voice means editing that map and calling `workflows update`; there is no dedicated command.
  The generator currently accepts these locales: `de-de`, `en-gb`, `en-us`, `es-es`, `es-mx`, `fr-fr`, `ja-jp`, `ko-kr`, `pt-br`, `pt-pt`, `zh-cn`.

## Designing a workflow

A workflow is a directed graph. Use `onepin nodes list` for the authoritative slugs and ports; the
shape below is the design contract.

**Overall shape:** one or more **Sources** → **Processing** → **Generator(s)** → **Validator(s)** →
one or more **Sinks**. A graph can have **multiple** sources, processors, generators, and sinks — it
is not a single linear chain.

**Example topologies (simple → robust):**
- **Minimal:** `source → generator → sink`.
- **+ accuracy:** `source → normalizer → generator → sink`.
- **Higher accuracy:** `source → normalizer → multiple generators → multiple validators → sink(s)`.
- **Fan-out:** a single source can feed several branches at once — e.g. `source → normalizer →
  generator` **and** the same source straight into a second `generator`, with both branches
  converging on sinks.

**Processor ordering:** the **Normalizer** typically runs *before* a generator (normalize text → then
TTS).

**Validators:**
- Can be wired **in series** (chained checks) or **in parallel** (independent checks on the same audio).
- Each exposes **pass / fail pins** plus a retry counter (default threshold 85, max-retry guard).
- A **fail pin** can route back to the *same* generator (regenerate) **or** forward to a *different /
  new* generator — failed items don't have to return to where they came from.

**After validation:**
- Most often validator results flow into a **Sink**.
- But results may also feed **another set of generators** for a further pass — validation is not
  necessarily terminal.

**Sinks:**
- A workflow can have **multiple** sinks.
- **Export** (`sink_preview`) is the default sink. If the user does **not** want results stored in
  Onepin and instead wants them in a **local directory**, run the workflow then pull outputs down with
  `onepin workflows runs download <workflow_id> <run_id> --out <path>` (and `runs data` for rows).

**Always discover first:** `nodes list` → `nodes show <slug>` → `definition-schema` before authoring.
Never invent slugs or ports.

## Recipe: upload a file and attach it

```bash
onepin --json uploads create --file script.txt --category script   # uploads via presigned S3, prints an id
onepin --json uploads confirm <upload_id> --workflow-id <workflow_id>
```

## Recipe: run and collect outputs

```bash
onepin --json workflows preview-run <workflow_id>                       # estimate cost
onepin --json workflows run <workflow_id> --watch --timeout 300         # run + wait (billable)
onepin --json workflows runs data <workflow_id> <run_id>                # output rows
onepin workflows runs download <workflow_id> <run_id> --out export.zip  # full export (atomic; --force to overwrite)
onepin workflows runs download-node <workflow_id> <run_id> <node_id> --out node.zip   # one node's output
```

`workflows run` also takes **run-scoped script inputs**: `--script "<text>"` replaces the saved
script for that one run (the workflow is not modified), and `--source-language <bcp-47>` (e.g.
`en-us`) declares the language of that text when it differs from the saved one. Use this for
one-off lines instead of `workflows update`.

## Recipe: diagnose a run

```bash
onepin --json workflows runs status <workflow_id> <run_id>     # terminal state only (cheap poll)
onepin --json workflows runs overview <workflow_id> <run_id>   # per-node rollup
onepin --json workflows runs steps <workflow_id> <run_id>      # steps; lightweight by default
onepin --json workflows runs steps <workflow_id> <run_id> --node-id <node_id> --include-result
```

`runs steps` returns **lightweight** step records unless `--include-result` is passed; `--node-type`
and `--node-id` filter and can be combined. Fetch the rollup first, then pull full results only for
the node that actually failed — `--include-result` across every step of a large run is a lot of
payload for nothing. `runs summary <workflow_id> --from <iso> --to <iso>` aggregates *across* runs.

## Audio surfaces

| What you want | Command | Field that carries it |
|---|---|---|
| a voice's sample **in a given language** | `voices list --language <code> [--search <name>]` | `language_sample_url` (+ `language_sample_locale` — the region actually served) |
| a voice's default sample | `voices list` · `voices show <voice_id>` | `sample_url` — does **not** follow `--language`, so it may be another language |
| a run's **per-line** audio | `workflows runs data <workflow_id> <run_id>` | `rows[].cards[].audio.playback_url` |
| files on disk | `workflows runs download` · `runs download-node` | the written file |

Every URL here is presigned and expires in about an hour — re-run the command to re-sign rather
than caching it. Read the statuses before claiming delivery: `audio.status` is `available` /
`not_ready` / `unsupported` / `unavailable`, and a `playback_url` is only expected on `available`
(treat a missing one as a line the user did not get, whatever the status says);
`card.status` is `delivered` / `generated` / `not_delivered` / `dropped`; envelope-level
`partial.status` (with `reason`, `source`) and `dropped_truncated` mean the page is incomplete.

**Not on the CLI:** the SDK additionally has `client.voices.preview(voice_id, language=…, model=…)`
and `client.workflows.get_run_audio_url(workflow_id, run_id, audio_id)`, but no `onepin` command
maps to either — use the table above instead of inventing a flag.

## Recipe: hand over a run's audio

```bash
onepin --json workflows runs data <workflow_id> <run_id> \
  | jq -r '.rows[].cards[]
           | select(.audio.status == "available")
           | [.line_index, .locale_code, .voice.display_name, .audio.playback_url] | @tsv'
```

Announce the line, then play it (or link it — `[▶ Line <line_index>](<playback_url>)`, never the
bare URL):

```bash
curl -fsSL "<playback_url>" -o /tmp/onepin-line.mp3 && afplay /tmp/onepin-line.mp3   # macOS
```

Cards also carry `validations[]` and `retry_count`, so a line that passed on a retry can be reported
as such. A card with no `playback_url`, or a `dropped` / `rejected` card, is a line the user did not
get — say so rather than letting a short list read as the whole run.

## Filters & pagination

List commands take `--limit` (default 50, **max ~100** — larger values return `422`), `--search`
(substring), and where shown `--sort`/`--order`/`--status`/`--category`. Most take **no offset or
cursor**, so a set larger than one page cannot be fully enumerated — narrow with filters and tell
the user when a list is partial. Two commands are paged and *can* be walked: `workflows runs data`
(`--limit` / `--offset`) and `usage activity` (`--limit` / `--cursor`). `voices list --language`
accepts only specific codes (e.g. `en-us`, `en-gb`, `en`); unsupported codes (e.g. `en-au`) return
`422`, even when voices report them in `supported_languages`.

## Errors

`--json` failures print `{"error":{"code","message"}}` to **stderr** with a non-zero exit; success
data goes to stdout. Key off the exit code (0 → stdout, non-zero → stderr envelope). Common codes:
`NOT_LOGGED_IN`, `INVALID_API_KEY`, `NOT_FOUND`, `VALIDATION_ERROR`, `FORBIDDEN`, `RATE_LIMITED`,
`CONFIRMATION_REQUIRED`.
