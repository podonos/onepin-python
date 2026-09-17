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

## Nodes: ask the catalog, don't read a table

Node knowledge comes from the API, not from a table in this file. Copies rot: the labels here were
wrong within a week of being written (`Phoneme Injector` is now `Phonemizer`), the catalog is edited
by staff without a deploy, and it is gated per workspace plan — so a frozen table can be wrong in a
way that is invisible until a graph is rejected. Three calls answer different halves of the
question:

```bash
# the whole catalog, one row per node
onepin --json nodes list \
  | jq -r '.[] | [.node_type, (.display_name + (if .beta then " (beta)" else "" end)),
                  (if (.outputs|length) == 0 then "-" else (.outputs|map(.name)|join("/")) end),
                  ((.config_schema // {}) | keys | join(","))] | @tsv' \
  | column -t -s$'\t'

# one node's config keys, with defaults, ranges and enums
onepin --json nodes list | jq '.[] | select(.node_type == "validator_error_rate") | .config_schema'
```

**1. `nodes list`** — per node: `node_type`, `display_name`, `description`, `version`, `beta`, the
`inputs` / `outputs` port names, `input_schema` (including the locale enum the generator accepts) and
`config_schema`. Note `config_schema` is a bare `name → schema` map, *not* a JSON-Schema object with
a `properties` key. **Never author with a slug `nodes list` did not return** — it may exist in the
enum and still be unavailable to this workspace.

**2. `workflows definition-schema`** — how nodes are *wired*, which `nodes list` says nothing about:
`graph.nodes[]` (`id`, `type`, `position`, `config`, `config_version`, `name`) and `graph.edges[]`
(`id`, `source`, `sourcePort`, `target`, `targetPort`, all required). The port names in an edge are
the ones `nodes list` gave you — `lines` for the line-carrying ports, `pass` / `fail` on validators.

**3. `nodes show <node_type>`** — adds `category` and `options`, the runtime side of a node. The
options are **hrefs, not inline data** (`{"kind": "href", "target": "/api/v1/voices", ...}`), and the
useful part is each href's `properties`: for `operator_generator` that is the complete set of valid
filter values — the locales, the providers, and the models, each with a display name. That is the
authoritative answer to "which model can I put in a `voice_map`". Follow the `voices` href with
`onepin voices list`; the `providers` href (`/api/v1/providers`) has no CLI command, but a voice
row's `supported_models` covers the same ground.

One caveat on when you can call it: the *endpoint* needs no valid credential, but the *CLI* refuses
to run any command without one, so `nodes list` works with an expired or even nonsense key but not
with no key at all.

### What the catalog does not tell you

- **Where a voice lives, and how to fill it in.** `operator_generator.config.voice_map` is a map of
  locale → list of `VoiceAssignment` (required: `voice_id`, `provider`, `model`; optional:
  `catalog_voice_id`, `voice_name`, `provider_config`, `canonical_controls`). Every field comes from
  a `voices list` row, and the two id fields are **not** interchangeable:

  | `VoiceAssignment` | `voices list` row |
  |---|---|
  | `voice_id` | `provider_voice_id` (the provider's own id, e.g. `"vdaeseong"`) |
  | `catalog_voice_id` | `id` (the catalog UUID) |
  | `provider` | `provider` |
  | `model` | one of `supported_models` — check `model_capabilities[]` lists the locale you are wiring |
  | `voice_name` | `name` (display only) |

  Changing a workflow's voice means editing that map and calling `workflows update` — there is no
  set-voice command.
- **That validator defaults are not uniform.** They differ per validator and are clamped to
  different ranges, so read the `threshold` default from `config_schema` and quote *that* number to
  the user rather than saying "the default".
- **What the pass/fail pins are for.** Validators expose two outputs; the routing rules are below.

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

Announce what is about to play, then play the run — in `line_index` order, without stopping to ask
between lines:

```bash
onepin --json workflows runs data <workflow_id> <run_id> \
  | jq -r '.rows[].cards[]
           | select(.audio.status == "available")
           | [.line_index, .audio.playback_url] | @tsv' \
  | sort -n \
  | while IFS=$'\t' read -r idx url; do
      announce "$idx"; play "$url"      # SKILL.md > Audio: whatever player this machine actually has
    done
```

Only when there is no audio device does this become links — `[▶ Line <line_index>](<playback_url>)`,
one per line, never the bare URL. Downloading the clips and pointing the user at the folder is not
the third option; it is the run undelivered.

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
