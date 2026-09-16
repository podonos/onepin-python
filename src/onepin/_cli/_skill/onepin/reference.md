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
  set-voice command, and no `--voice` on `workflows run` either, so there is no run-scoped way to
  swap a voice. The edit is permanent; `workflows duplicate` first if the original must survive.
  Both paths need the user's yes (SKILL.md → *Changing a voice is not run-scoped*).
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
onepin --json workflows preview-run <workflow_id> --script "<text>"     # estimate cost (no run)
onepin --json workflows run <workflow_id> --watch --timeout 300         # run + wait (billable)
onepin --json workflows runs data <workflow_id> <run_id>                # output rows
onepin workflows runs download <workflow_id> <run_id> --out export.zip  # full export (atomic; --force to overwrite)
onepin workflows runs download-node <workflow_id> <run_id> <node_id> --out node.zip   # one node's output
```

`workflows run` is **not** `--yes`-gated even though it spends credits — confirm with the user
first, every time, by the procedure in SKILL.md → *Running a workflow*. `preview-run` returns
`min_credits` / `expected_credits` / `max_credits` per node, and takes the same
`--script` / `--source-language` as `run` — pass them, or you price the saved definition instead of
the run being charged (and an unfilled script node priced without `--script` returns
`VALIDATION_ERROR`, since there is no text to count). If it still fails, don't drop the cost — fall
back to a past run's `credits` field on
`onepin --json workflows runs list <workflow_id>`, or failing that to the script's character count
(~1 credit/character for one Latin-script locale — a floor: extra locales multiply, CJK on a
byte-priced model runs ~3×, a translator adds a language multiplier). Label the number an estimate.

**Billing is per-unit, and the unit differs per node** — `character` for the text nodes, `byte` for a
TTS model priced in UTF-8 bytes, `word` for the pronunciation corrector — so no single rate
reproduces a charge exactly. A settled run also carries a per-run 1-credit floor. That is why the
estimate above is a floor and must be presented as one.

`workflows run` also takes **run-scoped script inputs**: `--script "<text>"` replaces the saved
script for that one run (the workflow is not modified), and `--source-language <bcp-47>` (e.g.
`en-us`) declares the language of that text when it differs from the saved one. Use this for
one-off lines instead of `workflows update`. `preview-run` accepts the identical pair and sends a
byte-identical body, so an estimate taken with the same flags prices the run that will be charged. Which of the two you are doing is one of the four
things the run confirmation has to state. Note what is *not* on that list: there is no `--voice`, so
a voice swap is always an edit to the saved definition, never a property of one run.

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
| a voice's sample **in a given language** | `voices list --language <code> [--search "<description>"]` | `language_sample_url` (+ `language_sample_locale` — the region actually served) |
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

## Recipe: shortlist a voice

Let the server narrow it; don't page the catalog (SKILL.md → *Let the server pick the shortlist*).

```bash
onepin --json voices list --language ko-kr --gender female \
  --search "calm, warm audiobook narrator" --limit 10 \
  | jq -r '.[] | [.name, .provider, (.age // "-"), (.category // "-"), .language_sample_url] | @tsv'
```

`--search` is a relevance-ranked query over meaning plus name/tags/descriptor, so pass the user's
own words rather than guessing a name. `age` / `category` / `accent` / `tags` come back on every row
even though no flag filters on them — refine on those *after* the server has narrowed, and say so,
because it only reorders the page you were given. Nothing matched? Drop `--search` first, then one
filter at a time. Then audition: `language_sample_url` is the clip in the locale you asked for, and
`voices similar <voice_id> --language <code>` is the server-side "more like this one".

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

List commands take `--limit` (default 50, **max ~100** — larger values return `422`), `--search`,
and where shown `--sort`/`--order`/`--status`/`--category`. `workflows list`, `workflows runs list`,
`templates list`, `voices list` and `workflows runs data` also take `--offset`, so a set larger than
one page is walked with `--offset 100`, `--offset 200`, … (`usage activity` pages with `--cursor`
instead; `nodes list` and `workspace members list` are unpaged.) Text output ends with
`Showing X of N`, where `N` is the unpaginated match count — use it to decide whether another page
exists rather than guessing from a full one. `--json` returns the rows alone.

**Every filter is evaluated server-side.** The CLI forwards them as query parameters and renders
what comes back, so filtering is the only thing that makes a list mean anything. It also renders
*only the rows* — the response's pagination envelope is dropped — so no list command reports a
total. A short list is "what this page held", never "this is all there is".

**`voices list --search` is the one that is easy to underestimate.** `onepin schema` describes it as
a substring search; the server actually matches the query against a voice's meaning as well as its
name, tags and descriptor, and returns the result relevance-ranked — so a phrase like
`"warm, unhurried documentary narrator"` is a better query than a guessed name. `schema` is
authoritative on *which flags exist and what shape they take*; it is not a description of how the
server matches them. See SKILL.md → *Let the server pick the shortlist*.

`voices list --language` accepts only specific codes (e.g. `en-us`, `en-gb`, `en`); unsupported
codes (e.g. `en-au`) return `422`, even when voices report them in `supported_languages`. Passing it
also fills `language_sample_url` / `language_sample_locale` on every row it has a clip for.

## Errors

`--json` failures print `{"error":{"code","message"}}` to **stderr** with a non-zero exit; success
data goes to stdout. Key off the exit code (0 → stdout, non-zero → stderr envelope). Common codes:
`NOT_LOGGED_IN`, `INVALID_API_KEY`, `NOT_FOUND`, `VALIDATION_ERROR`, `FORBIDDEN`, `RATE_LIMITED`,
`CONFIRMATION_REQUIRED`.
