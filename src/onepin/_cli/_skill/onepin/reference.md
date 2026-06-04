# OnePin CLI reference

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
| `workspace` | `list`, `show`, `create`, `update`, `delete`, `settings`; subgroups `members`, `stats` |
| `workspace members` | `list`, `invite`, `set-role`, `remove`, `accept`, `invite-role`, `revoke-invite` |
| `workspace stats` | `runs`, `workflows` (accept `--from`/`--to` ISO datetimes) |
| `usage` | `summary`, `by-language`, `activity` (`--range 30d/60d/90d`) |
| `provider-keys` | `list`, `put <provider>`, `delete <provider>` (secrets are redacted on read) |
| `nodes` | `list`, `show <node_type>` (workflow node types + runtime options) |
| `health` | `live`, `ready` |
| `auth` | `login`, `logout`, `whoami` |
| `schema` | the JSON manifest (the contract) |

## Destructive commands (need `--yes`; confirm with the user first)

`workflows delete` · `workflows runs cancel` · `templates delete` · `uploads delete` ·
`workspace delete` · `workspace members remove` · `workspace members revoke-invite` ·
`provider-keys delete`. Under `--json` without `--yes` they return `CONFIRMATION_REQUIRED` — that
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
