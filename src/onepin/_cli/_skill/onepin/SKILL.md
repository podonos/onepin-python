---
name: onepin
description: >-
  Use when the user mentions OnePin or wants to operate a OnePin voice-workflow
  workspace from the terminal — list / inspect / run workflows, check run status,
  browse voices or templates, inspect usage. OnePin is an AI voice-workflow
  platform with a `onepin` CLI; this skill drives it safely.
---

# OnePin

Drive a OnePin voice-workflow workspace through the `onepin` CLI. The CLI is the only
integration surface — this skill teaches its contract, not a frozen command list.

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
     (mint a key at https://app.onepin.ai/settings/api-keys), then stop.
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
rather than dumping raw JSON.

### Workflows
- List: `onepin --json workflows list` — filters `--status`, `--search`, `--sort`, `--order`,
  `--limit`. **Lists are paginated and truncated:** default `--limit` is 50, the max page is ~100
  (larger values return `422 VALIDATION_ERROR`), and there is no offset/cursor — so a large set
  cannot be fully enumerated. Narrow with `--search`/filters; if results are capped, tell the user
  the list is partial rather than implying it is complete.
- Inspect: `onepin --json workflows show <workflow_id>`
- Estimate cost before running: `onepin --json workflows preview-run <workflow_id>`
- **Run (starts a real, billable execution):** `onepin --json workflows run <workflow_id>`. A run
  consumes credits and acts on the live workspace. It is *not* `--yes`-gated, so for an expensive,
  production, or ambiguous run, confirm with the user first (and consider `preview-run`).
- Run and wait: `onepin --json workflows run <workflow_id> --watch --timeout 300` — polls to a
  terminal state (`completed`/`failed`/`cancelled`) and returns the final status inline (no
  separate status call). Exit is non-zero if the run failed or timed out.
- **Build/design a workflow:** see the GA node catalog and the *Designing a workflow* topology rules
  (sources → processing → generators → validators → sinks; validator pass/fail pins and retries) in
  [reference.md](reference.md). Discover slugs with `onepin nodes list` — never invent them.

### Runs
- `onepin --json workflows runs list <workflow_id>`
- `onepin --json workflows runs status <workflow_id> <run_id>`
- `onepin --json workflows runs data <workflow_id> <run_id>` (output rows)
- Download outputs to a file: `onepin workflows runs download <workflow_id> <run_id> --out export.zip`
  (atomic; refuses to overwrite without `--force`).

### Voices
- `onepin --json voices list` — filters `--provider`, `--gender`, `--language`, `--search`.
  `--language` accepts only specific comma-separated codes (e.g. `en-us`, `en-gb`, `en`); an
  unsupported code returns `422` — don't guess regions, and note a voice's own
  `supported_languages` may be broader than the filter codes. Same pagination cap as above
  (default 50, ~100 max, no offset), so the full catalog can't be listed in one call.
- `onepin --json voices show <voice_id>` · `onepin --json voices similar <voice_id>`

### Templates
- `onepin --json templates list` — filters `--category`, `--sort`, `--search`
- `onepin --json templates show <template_id>`

## Destructive operations (require explicit confirmation)

`workflows delete`, `templates delete`, `uploads delete`, `workspace delete`,
`provider-keys delete`, `workflows runs cancel`, `workspace members remove`,
`workspace members revoke-invite` — all irreversible. Procedure:

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
usage, provider-keys, nodes, health), see [reference.md](reference.md) or run `onepin schema`.
