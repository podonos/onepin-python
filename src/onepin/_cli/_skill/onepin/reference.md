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
| `schema` | the JSON manifest (the contract) |

## Destructive commands (need `--yes`; confirm with the user first)

`workflows delete` · `workflows runs cancel` · `templates delete` · `uploads delete` ·
`workspace delete` · `workspace members remove` · `workspace members revoke-invite`.
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

## Node catalog (generally-available nodes)

`onepin nodes list` is **authoritative** for the exact `node_type` slug, ports, and config schema —
confirm the slug via `nodes list` / `nodes show <slug>` before authoring. This is a conceptual map
of the GA nodes (keyed by display name + category), not a slug reference.

| Node | Category | Purpose | Key config |
|------|----------|---------|------------|
| **Single script input** | source | Entry point; emits one script in one locale to its output. | script text / `.txt`/`.csv` |
| **Normalizer** | processing | Text normalization before TTS (e.g. `"123 main st."` → `"one two three main street"`); multilingual. | language code |
| **Voice Generator** | processing | TTS for one script in one locale → an audio object. **24 TTS models** across providers, each with different config support and pricing (the spread from cheapest-but-reasonable to most expensive is ~40×). | **auto-route** picks the best model for the language/locale from Onepin's TTS benchmark, balancing performance against price, or set provider + model manually; speed, emotion, tone, and more (model-dependent) |
| **Validator – Word accuracy** | validation | ASR-based word accuracy in [0, 100] (from WER); emits **pass** / **fail** pins. | threshold (default 85, adjustable), max-retry |
| **Validator – Naturalness** | validation | Internal-AI naturalness score in [0, 100]; emits **pass** / **fail** pins. | threshold (default 85, adjustable), max-retry |
| **Onepin storage** | output (sink) | Aggregates audio + scripts + validation results for download/visualization. | — |

Every validator's pass/fail **threshold is adjustable**. Validators also carry a per-object **retry
counter**: each visit increments it; once it reaches max-retry the object exits the **pass** pin
regardless of score, which prevents infinite loops.

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
- **Onepin storage** is the default sink. If the user does **not** want results stored in Onepin and
  instead wants them in a **local directory**, run the workflow then pull outputs down with
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
```

## Filters & pagination

List commands take `--limit` (default 50, **max ~100** — larger values return `422`), `--search`
(substring), and where shown `--sort`/`--order`/`--status`/`--category`. There is **no offset or
cursor**, so a set larger than one page cannot be fully enumerated — narrow with filters and tell
the user when a list is partial. `voices list --language` accepts only specific codes (e.g.
`en-us`, `en-gb`, `en`); unsupported codes (e.g. `en-au`) return `422`, even when voices report
them in `supported_languages`.

## Errors

`--json` failures print `{"error":{"code","message"}}` to **stderr** with a non-zero exit; success
data goes to stdout. Key off the exit code (0 → stdout, non-zero → stderr envelope). Common codes:
`NOT_LOGGED_IN`, `INVALID_API_KEY`, `NOT_FOUND`, `VALIDATION_ERROR`, `FORBIDDEN`, `RATE_LIMITED`,
`CONFIRMATION_REQUIRED`.
