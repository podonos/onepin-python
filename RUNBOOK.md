# RUNBOOK — onepin-python

Rollback and incident procedures for the public `onepin` package on PyPI.

Operations-internal procedures (secret rotation, alerting channels, upstream
spec-repo workflow) live in a separate private runbook and are not duplicated
here.

## Bad SDK on PyPI

Use `twine yank` (PEP 592). Yanked versions are skipped for new installs but
still reachable by pinned requirements. **Never** use `twine delete` — PyPI
deletions are irrevocable.

```bash
# Yank a broken release
twine yank onepin==0.1.3 --reason "broken upload flow — install 0.1.4 instead"

# Unyank if the concern was a false alarm
twine unyank onepin==0.1.3
```

## Bad tag (not yet on PyPI)

A bad tag reaches **TestPyPI** via `publish.yml` but does **not** reach customers until a
prod promote (`promote-prod.yml`). Deleting the tag is viable any time before that promote
runs. After the version is on **PyPI**, the tag delete no longer helps — use `twine yank`
instead (and PyPI's immutable index / the promote preflight already block a re-upload).

```bash
git tag -d v0.X.Y
git push --delete origin v0.X.Y
```

## Bad release-please PR

Close the PR. The bot recreates it on the next push to `main` with a rebased
state.

## SDK regeneration introduced a regression

Revert the merged regeneration PR on `onepin-python`. The next event-driven
regen will produce a fresh PR with the corrected SDK.

## CI / publish pipeline failures

Check the failed action run linked from the workflow status on the relevant PR
or tag. Most failures fall into one of:

- Lint / test failure on a supported Python version → fix on the branch.
- TestPyPI upload error → inspect the `publish.yml` job logs and re-trigger.
- PyPI upload error → inspect the `promote-prod.yml` job logs and re-trigger.
- Attestation verification failure → confirm the `--repo` flag is scoped
  correctly in `promote-prod.yml`.
- Insane version (`0.0.0` / `+local`) → a shallow/tagless checkout starved
  hatch-vcs; the build asserts and aborts. Confirm the job checks out with
  `fetch-depth: 0` + `fetch-tags: true`.

## The two publish lanes

The package publishes from **two independent lanes** (full model + diagram:
[`docs/PUBLISH.md`](docs/PUBLISH.md)):

- **TestPyPI lane — `publish.yml`** (continuous, internal). Fires on push to `main`
  (touching `src/onepin/**`, `pyproject.toml`, `uv.lock`), on a release tag, or via
  `workflow_dispatch`. hatch-vcs stamps `X.Y.Z.devN` on main / clean `X.Y.Z` on a tag,
  asserts the version is sane, and publishes to **TestPyPI only** (`skip-existing`).
- **PyPI lane — `promote-prod.yml`** (customers, prod-gated). Fires on
  `repository_dispatch[api-spec-updated]` **only when `environment == 'prod'`** (the
  backend production deploy dispatch), or manually via `workflow_dispatch`.
  Resolves the latest `vX.Y.Z` tag, builds a clean `X.Y.Z`, runs the immutable-index
  preflight, then publishes to **PyPI** (OIDC trusted publishing + provenance).

> **PyPI Trusted Publisher prereq:** the `onepin` PyPI project's Trusted Publisher must
> point at workflow filename **`promote-prod.yml`** with environment **`pypi`** (it was
> `publish.yml`). This is a one-time manual change in the PyPI project settings — until
> it lands, the `pypi` OIDC mint is rejected. See `docs/PUBLISH.md`.

## Publishing a release

Merging the release-please PR tags the version; **`publish.yml`** then builds → **TestPyPI**.
The customer-facing **PyPI** publish happens separately in **`promote-prod.yml`**, gated on a
real backend **prod** deploy dispatch (or a manual promote).

Auto-publish on the tag requires the **`RELEASE_PAT`** repo secret. release-please uses this
token for **all** its GitHub calls, so it needs both `contents: write` (to push the tag, which
fires `publish.yml`'s `push: tags` trigger) **and** `pull requests: write` (to create/update
the release PR) — a `contents`-only PAT fails the next release-please run before any tag is
cut. Without the secret nothing publishes; release-please falls back to the default token. Use
a fine-grained PAT scoped to `podonos/onepin-python` only, with an expiry; rotation is tracked
in the private ops runbook.

The PyPI lane is additionally gated on the **`onepin-pipeline-bot` GitHub App** (org secrets
`PIPELINE_APP_ID` / `PIPELINE_APP_PRIVATE_KEY`). If the App is absent at a real prod deploy,
`promote-prod.yml` warn-skips — replay the missed release manually once the App exists (below).

Manual fallback — **TestPyPI** (publish an existing ref):

```bash
# Dispatch from a ref that has the CURRENT workflow (main). publish.yml derives the
# version from hatch-vcs at the checked-out ref (no tag input — the version is dynamic).
gh workflow run publish.yml --ref main
```

Manual fallback / replay — **PyPI** (promote an existing release tag to customers):

```bash
# Used when the pipeline App was absent at the prod deploy, or to re-drive a promote.
# Supplying -f tag= bypasses the per-sha ancestry resolver (human override).
# The preflight refuses a version that already exists on PyPI.
gh workflow run promote-prod.yml --ref main -f tag=vX.Y.Z
```

> **First prod promote (migration):** tags cut before `.spec-sha` was introduced carry no
> `.spec-sha` file. The per-sha resolver skips them all and aborts — this is correct
> (fail-closed). Use `workflow_dispatch -f tag=vX.Y.Z` (the manual path above) for the
> first promote; it skips the ancestry check. Once a new `feat:` regen tag carrying
> `.spec-sha` exists, automated prod dispatches resolve normally.
