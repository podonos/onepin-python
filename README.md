# onepin

Python SDK + CLI for [OnePin](https://onepin.ai) — the AI-powered voice workflow platform.

[![PyPI version](https://img.shields.io/pypi/v/onepin)](https://pypi.org/project/onepin/)
[![Python versions](https://img.shields.io/pypi/pyversions/onepin)](https://pypi.org/project/onepin/)
[![CI](https://github.com/podonos/onepin-python/actions/workflows/ci.yml/badge.svg)](https://github.com/podonos/onepin-python/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Installation

```bash
pip install onepin
```

Installs both the `onepin` Python SDK and the `onepin` command-line tool.

Full documentation: [docs.onepin.ai](https://docs.onepin.ai)

## Authentication

Mint an API key at [app.onepin.ai/settings/api-keys](https://app.onepin.ai/settings/api-keys), then:

```bash
onepin login
# Paste your key when prompted — validated, then saved to ~/.onepin/credentials (mode 0600)

onepin whoami      # Show the active auth source, workspace UUID, and key scopes
onepin logout      # Remove stored credentials
```

Credential resolution order: `--api-key` flag → `ONEPIN_API_KEY` env var → stored `~/.onepin/credentials`.

## Use from your AI coding tool

OnePin ships an [Agent Skill](https://agentskills.io) that teaches AI coding tools to drive the
`onepin` CLI for you — list and run workflows, check run status, browse voices and templates —
without leaving your editor. It works in Claude Code, Cursor, OpenAI Codex, Gemini CLI, and GitHub
Copilot. Install it with the CLI (it auto-detects which tools you have):

```bash
onepin skill install                                # every detected tool
onepin skill install --tool claude --tool cursor    # or pick tools explicitly
onepin skill install --all                          # every supported tool
onepin skill install --project                      # into ./ (this repo) instead of your home dir
onepin skill path                                   # show where it is / would be installed
onepin skill uninstall                              # remove it
```

In **Claude Code** the skill is then invocable as `/onepin`; other tools load it automatically when
your request is about OnePin. After the first install, restart your tool (or run `/reload-plugins`
in Claude Code) so it picks up the new skills directory. The skill drives the same `onepin` CLI, so
run `onepin login` first.

## Version compatibility

The OnePin API advertises the minimum SDK version it still accepts. When a response indicates your
installed `onepin` is **below that floor**, the SDK stops with a clear, copy-paste upgrade message:

```
onepin 0.4.1 is below the required minimum 0.5.0. Upgrade: pip install --upgrade 'onepin>=0.5.0'
```

The `onepin` CLI enforces this automatically. For **programmatic** use, build the client with
`onepin.make_client` (instead of `OnePinClient` directly) to get the same gate plus a corrected
`User-Agent`:

```python
import onepin

client = onepin.make_client(token="op_live_...")
client.workflows.list()  # raises onepin.OnePinUpgradeRequiredError if the SDK is too old
```

The CLI also nudges you when a newer release is available on PyPI (surfaced through the OnePin agent
skill). Set `ONEPIN_NO_UPDATE_CHECK=1` to silence the recommended-upgrade check.

## Command reference

The CLI groups its commands by resource. Every group prints its own command list with
`onepin <group> --help`, and each command lists its flags with `onepin <group> <command> --help`.
The examples further below are representative; the **authoritative, exhaustive inventory** is
generated from the live command tree (the same source as `onepin schema`) and kept in sync by CI:

<!-- BEGIN GENERATED: cli-commands -->
## CLI command reference

### health

- `onepin health live` — Liveness probe.
- `onepin health ready` — Readiness probe.

### login

- `onepin login` — Validate an API key and write it to ~/.onepin/credentials.

### logout

- `onepin logout` — Remove ~/.onepin/credentials.

### nodes

- `onepin nodes list` — List available node types.
- `onepin nodes show <node_type>` — Show a node type's detail (runtime options).

### provider-keys

- `onepin provider-keys delete <provider>` — Delete a provider key.
- `onepin provider-keys list` — List configured provider keys.
- `onepin provider-keys put <provider>` — Create or replace a provider key.

### schema

- `onepin schema` — Emit the machine-readable JSON manifest of all commands.

### skill

- `onepin skill install` — Install the OnePin agent skill (Claude Code, Cursor, Codex, Gemini, Copilot).
- `onepin skill path` — Show where the skill is or would be installed.
- `onepin skill uninstall` — Remove the installed OnePin agent skill.

### templates

- `onepin templates clone <template_id>` — Clone a template into a new workflow.
- `onepin templates create` — Create a template.
- `onepin templates delete <template_id>` — Delete a template.
- `onepin templates favorite <template_id>` — Favorite a template.
- `onepin templates list` — List gallery templates.
- `onepin templates show <template_id>` — Show a single template.
- `onepin templates unfavorite <template_id>` — Unfavorite a template.
- `onepin templates update <template_id>` — Update a template.

### uploads

- `onepin uploads confirm <upload_id>` — Confirm an upload and attach it to a workflow.
- `onepin uploads create` — Upload a file via the presigned-S3 flow.
- `onepin uploads delete <upload_id>` — Delete an upload.

### usage

- `onepin usage activity` — Recent workspace activity.
- `onepin usage by-language` — Usage broken down by language.
- `onepin usage summary` — Usage summary.

### voices

- `onepin voices favorite <voice_id>` — Favorite a voice.
- `onepin voices list` — List available voices.
- `onepin voices show <voice_id>` — Show a single voice.
- `onepin voices similar <voice_id>` — List voices similar to a voice.
- `onepin voices unfavorite <voice_id>` — Unfavorite a voice.

### whoami

- `onepin whoami` — Show active auth source + workspace UUID + scopes.

### workflows

- `onepin workflows create` — Create a workflow.
- `onepin workflows definition-schema` — Print the JSON Schema for a workflow definition.
- `onepin workflows delete <workflow_id>` — Delete a workflow.
- `onepin workflows duplicate <workflow_id>` — Duplicate a workflow.
- `onepin workflows list` — List workflows in the workspace.
- `onepin workflows preview-run <workflow_id>` — Estimate cost of a run without executing.
- `onepin workflows run <workflow_id>` — Start a workflow run, optionally watching to completion.
- `onepin workflows show <workflow_id>` — Show a single workflow.
- `onepin workflows update <workflow_id>` — Update a workflow (partial patch).
- `onepin workflows uploads <workflow_id>` — List a workflow's uploads.

#### workflows runs

- `onepin workflows runs cancel <workflow_id> <run_id>` — Cancel a running run.
- `onepin workflows runs data <workflow_id> <run_id>` — Show a run's output data.
- `onepin workflows runs download <workflow_id> <run_id>` — Download a run's full export to a file.
- `onepin workflows runs download-node <workflow_id> <run_id> <node_id>` — Download a single node's output to a file.
- `onepin workflows runs list <workflow_id>` — List runs for a workflow.
- `onepin workflows runs overview <workflow_id> <run_id>` — Show a run's node overview.
- `onepin workflows runs show <workflow_id> <run_id>` — Show a single run.
- `onepin workflows runs status <workflow_id> <run_id>` — Show a run's current status.
- `onepin workflows runs steps <workflow_id> <run_id>` — List the steps of a run.
- `onepin workflows runs summary <workflow_id>` — Summarize a workflow's runs.

### workspace

- `onepin workspace create` — Create a workspace.
- `onepin workspace delete <workspace_id>` — Delete a workspace.
- `onepin workspace list` — List workspaces.
- `onepin workspace settings <ws_id>` — Show a workspace's settings.
- `onepin workspace show <workspace_id>` — Show a workspace.
- `onepin workspace update <workspace_id>` — Update a workspace.

#### workspace members

- `onepin workspace members accept <token>` — Accept an invite by token.
- `onepin workspace members invite <ws_id>` — Invite a member.
- `onepin workspace members invite-role <ws_id> <invite_id>` — Change a pending invite's role.
- `onepin workspace members list <ws_id>` — List workspace members.
- `onepin workspace members remove <ws_id> <member_id>` — Remove a member.
- `onepin workspace members revoke-invite <ws_id> <invite_id>` — Revoke a pending invite.
- `onepin workspace members set-role <ws_id> <member_id>` — Change a member's role.

#### workspace stats

- `onepin workspace stats runs` — Workspace run statistics.
- `onepin workspace stats workflows` — Workspace workflow statistics.
<!-- END GENERATED: cli-commands -->

### Global flags

These apply to every command (pass them before the subcommand):

```
--api-key TEXT     API key for this invocation        (env: ONEPIN_API_KEY)
--base-url TEXT    Override the API base URL           (env: ONEPIN_BASE_URL)
--workspace TEXT   Workspace UUID to scope requests to (env: ONEPIN_WORKSPACE_ID)
--json             Emit machine-readable JSON to stdout instead of rich tables
--no-color         Disable ANSI coloring
-v, --verbose      Log HTTP requests/responses to stderr (auth/login flow only)
--debug            Verbose logging; implies --verbose (auth/login flow only)
--version          Show version and exit
```

`--verbose`/`--debug` only affect HTTP logging on the authentication path; they do not change
command output. Use `--json` for machine-consumable data on any command.

### auth — `login`, `logout`, `whoami`

```bash
onepin login
onepin whoami
onepin logout
```

### workflows — create, run, and inspect workflows

```bash
onepin workflows list --status running --sort updated_at --order desc
onepin workflows show <workflow_id>
onepin workflows create --name "My workflow" --definition @workflow.json
onepin workflows update <workflow_id> --name "Renamed"
onepin workflows duplicate <workflow_id>
onepin workflows preview-run <workflow_id>          # estimate cost without executing
onepin workflows run <workflow_id> --watch          # poll to a terminal state
onepin workflows definition-schema                  # JSON Schema for a definition
onepin workflows delete <workflow_id> --yes
```

See `onepin workflows --help` for the full list.

#### workflows runs — inspect and control runs

```bash
onepin workflows runs list <workflow_id>
onepin workflows runs show <workflow_id> <run_id>
onepin workflows runs status <workflow_id> <run_id>
onepin workflows runs steps <workflow_id> <run_id>
onepin workflows runs overview <workflow_id> <run_id>
onepin workflows runs data <workflow_id> <run_id>
onepin workflows runs summary <workflow_id>
onepin workflows runs cancel <workflow_id> <run_id> --yes
onepin workflows runs download <workflow_id> <run_id> --out export.zip
onepin workflows runs download-node <workflow_id> <run_id> <node_id> --out node.wav
```

See `onepin workflows runs --help` for the full list.

### templates — browse and manage gallery templates

```bash
onepin templates list --category media --sort popular
onepin templates show <template_id>
onepin templates clone <template_id> --name "My copy"
onepin templates create --name "Starter" --definition @template.json
onepin templates favorite <template_id>
```

See `onepin templates --help` for the full list (`update`, `delete`, `unfavorite`).

### voices — browse available voices

```bash
onepin voices list --provider elevenlabs --gender female --language en-us
onepin voices show <voice_id>
onepin voices similar <voice_id>
onepin voices favorite <voice_id>
```

See `onepin voices --help` for the full list.

### uploads — manage file uploads (presigned-S3 flow)

```bash
onepin uploads create --file script.txt --category script   # upload + presign in one step
onepin uploads confirm <upload_id> --workflow-id <workflow_id>
onepin uploads delete <upload_id> --yes
```

See `onepin uploads --help` for the full list.

### workspace — manage workspaces, members, and statistics

```bash
onepin workspace list
onepin workspace show <workspace_id>
onepin workspace create --name "Team"
onepin workspace update <workspace_id> --name "Renamed"
onepin workspace settings <ws_id>
onepin workspace delete <workspace_id> --yes
```

See `onepin workspace --help` for the full list.

#### workspace members — members and invites

```bash
onepin workspace members list <ws_id>
onepin workspace members invite <ws_id> --email user@example.com --role editor
onepin workspace members set-role <ws_id> <member_id> --role admin
onepin workspace members remove <ws_id> <member_id> --yes
onepin workspace members accept <token>
```

See `onepin workspace members --help` for the full list (`invite-role`, `revoke-invite`).

#### workspace stats — aggregate statistics

```bash
onepin workspace stats runs --from 2026-01-01 --to 2026-02-01
onepin workspace stats workflows
```

### usage — inspect workspace usage and activity

```bash
onepin usage summary --range 30d
onepin usage activity --type workflow_run --limit 50
onepin usage by-language --range 90d
```

See `onepin usage --help` for the full list.

### provider-keys — manage bring-your-own-key credentials

```bash
onepin provider-keys list
onepin provider-keys put <provider> --key '{"api_key": "..."}'
onepin provider-keys delete <provider> --yes
```

Stored credentials are never echoed back; reads return redacted metadata only.

### nodes — inspect available workflow node types

```bash
onepin nodes list
onepin nodes show <node_type>
```

### health — API liveness and readiness probes

```bash
onepin health live
onepin health ready
```

### schema — machine-readable command manifest

```bash
onepin schema --json
```

## For agents / scripting

The CLI is designed to be driven programmatically.

### The command manifest is the contract

```bash
onepin schema --json
```

`schema` emits a stable, machine-readable JSON manifest of every command: each entry has a
`path` array (the full subcommand chain, e.g. `["workflows", "runs", "download"]`), its
positional `args`, its `options` (flag, type, required, default, help), and a `destructive`
flag. Build tooling against this manifest rather than scraping `--help`.

### Structured output and exit codes

Pass `--json` to any command to get raw data on **stdout**. When `--json` is set, a failure
writes a structured error envelope to **stderr** instead of the default `[CODE] message` line:

```json
{"error": {"code": "not_found", "message": "Workflow not found"}}
```

Exit codes:

| Code | Meaning                                  |
|------|------------------------------------------|
| 0    | Success                                  |
| 1    | API or runtime error                     |
| 2    | Usage error (bad flags/arguments)        |
| 130  | Interrupted (SIGINT)                     |

### Recipe: build a workflow definition

```bash
# 1. Discover the available node types
onepin nodes list

# 2. Inspect the ports/options of a node type
onepin nodes show <node_type>

# 3. Get the JSON Schema a definition must satisfy ...
onepin workflows definition-schema

#    ... or copy a known-good `.definition` from an existing template or workflow:
onepin templates show <template_id> --json
onepin workflows show <workflow_id> --json

# 4. Assemble your definition JSON into a file, then create the workflow
onepin workflows create --name "My workflow" --definition @workflow.json
```

`--definition` accepts inline JSON or `@path/to/file.json`. The same flag is available on
`workflows update`, `templates create`, and `templates update`.

## SDK usage

The Python SDK is generated by [Fern](https://buildwithfern.com) from the OpenAPI spec.
Full per-endpoint reference: [`src/onepin/reference.md`](src/onepin/reference.md) ·
hosted docs at [docs.onepin.ai](https://docs.onepin.ai). Runnable scripts in [`examples/`](examples/).

```python
from onepin import OnePinClient

client = OnePinClient(token="op_...")   # your API key, used as the bearer token

workflows = client.workflows.list()     # paginated — iterate items directly
voices = client.voices.list()
ready = client.health.readiness()
```

### Environments

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

# Defaults to PROD (https://api.onepin.ai). Target the dev API instead:
client = OnePinClient(token="op_...", environment=OnePinClientEnvironment.DEV)
# ...or point at any host directly:
client = OnePinClient(token="op_...", base_url="https://dev-api.onepin.ai")
```

### Async

```python
import asyncio
from onepin import AsyncOnePinClient

client = AsyncOnePinClient(token="op_...")


async def main() -> None:
    voices = await client.voices.list()


asyncio.run(main())
```

### Errors, retries, timeouts

```python
from onepin import OnePinClient
from onepin.core.api_error import ApiError

client = OnePinClient(token="op_...", timeout=20.0)   # client-wide timeout (default 60s)

try:
    client.workflows.get(
        workflow_id="wf_123",
        request_options={"max_retries": 1, "timeout_in_seconds": 5},
    )
except ApiError as e:
    print(e.status_code, e.body)
```

## Repository structure

- `src/onepin/` — Fern-generated SDK (do not hand-edit; overwritten on each regen)
- `src/onepin/_cli/` — hand-rolled Typer CLI atop the generated client
- `src/onepin/reference.md` — full per-endpoint API reference
- `examples/` — runnable SDK snippets
- `scripts/post_fern.sh` — restores `py.typed` markers after Fern overwrites `src/onepin/`

## License

MIT — see [LICENSE](LICENSE).

## Status

Published on PyPI — latest: **v0.6.0**. See the [changelog](CHANGELOG.md).
