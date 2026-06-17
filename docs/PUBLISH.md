# Publish pipeline — the two-lane model

`onepin` ships from **two independent publish lanes**. The split exists for one reason:
**internal iteration must be able to run ahead of customers, but customers (public PyPI)
must only ever receive a build that a real production deploy blessed.**

| | TestPyPI lane | PyPI lane |
|---|---|---|
| File | `.github/workflows/publish.yml` | `.github/workflows/promote-prod.yml` |
| Index | `test.pypi.org` (internal) | `pypi.org` (customers) |
| Cadence | **continuous** | **prod-gated** |
| Trigger | push to `main` (SDK inputs) · release tag `vX.Y.Z` · `workflow_dispatch` | `repository_dispatch[api-spec-updated]` with `environment == 'prod'` · `workflow_dispatch` |
| Version | `X.Y.Z.devN` on main · clean `X.Y.Z` on a tag (hatch-vcs) | clean `X.Y.Z` only (built from the release tag) |
| Gate | none (internal) | App-token guard **+** prod-environment trigger **+** PyPI preflight |

## Version ownership

- **Version source is dynamic** — `hatch-vcs` derives it from git tags + history at build
  time (`pyproject.toml`: `[project] dynamic = ["version"]`, `[tool.hatch.version] source = "vcs"`,
  `local_scheme = "no-local-version"`). There is **no `version =` string in any tracked file.**
- **release-please owns the SDK's own semver** (independent of the backend). It is configured
  `release-type: simple`, so it cuts `vX.Y.Z` tags from conventional commits and maintains
  `CHANGELOG.md` + `.release-please-manifest.json` — but writes **no version into source**
  (the `simple` updater only touches a `version.txt`, which this repo deliberately does not
  have). The regen PR is **`feat:`** (not `chore:`) so a merged regen actually bumps a release.
- The backend and the SDK version are **fully independent**. The backend prod
  deploy is purely the **publish timing gate** for the PyPI lane — it does not set the version.

## Flow diagram

```
                          ┌──────────────────────────── TestPyPI lane (continuous) ─────────────────────────┐
 backend dev/spec change  │                                                                                  │
        │                 │   regen.yml (feat: PR) ──merge──▶ main ──┐                                        │
        ▼                 │                                          │ push: src/onepin/**, pyproject, lock   │
 repository_dispatch ─────┤   release-please ──cuts──▶ tag vX.Y.Z ───┤                                        │
   (environment=dev,      │                                          ▼                                        │
    smoke-check only)     │                                  publish.yml                                      │
                          │                            fetch-depth:0 + hatch-vcs                              │
                          │                       main → X.Y.Z.devN  ·  tag → X.Y.Z                           │
                          │                       assert sane (no 0.0.0 / no +local)                          │
                          │                                          │                                        │
                          │                                          ▼                                        │
                          │                                    ✦ TestPyPI ✦  (skip-existing)                  │
                          └──────────────────────────────────────────────────────────────────────────────────┘

                          ┌──────────────────────────────── PyPI lane (prod gate) ──────────────────────────┐
 backend PROD deploy      │                                                                                  │
 (deploy-prod.yml)     ───┼─▶ repository_dispatch[api-spec-updated] {sha=S, spec_version, environment: prod} │
                          │                                  │                                               │
                          │                                  ▼                                               │
                          │                          promote-prod.yml                                        │
                          │      gate: App configured? + (environment==prod OR manual dispatch)              │
                          │      resolve (prod dispatch, per-sha pinning):                                   │
                          │        iterate vX.Y.Z tags newest-first:                                         │
                          │          read .spec-sha@<tag>  →  404/empty ⇒ skip (predates record)            │
                          │                                     other error ⇒ ABORT (fail closed)           │
                          │          compare(tag_spec...S) in spec repo:                                     │
                          │            ahead / identical ⇒ SAFE (API ≤ prod) → promote this tag             │
                          │            behind / diverged ⇒ skip (SDK ahead of prod)                         │
                          │            404 ⇒ skip (SHA GC'd); other error ⇒ ABORT (fail closed)             │
                          │        no tag passes ⇒ ABORT                                                     │
                          │      build resolved tag (fetch-depth:0, hatch-vcs → clean X.Y.Z)                │
                          │      assert ^[0-9]+\.[0-9]+\.[0-9]+$  (NO .devN / NO +local)                    │
                          │      preflight: GET pypi.org/pypi/onepin/<version>/json → 200 ⇒ abort           │
                          │                                  │                                               │
                          │                                  ▼                                               │
                          │              ✦ PyPI ✦  (OIDC trusted publishing, environment: pypi,             │
                          │                         build-provenance attestation)                           │
                          └──────────────────────────────────────────────────────────────────────────────────┘

 CLI-only change: release-please bumps Z → publish.yml → TestPyPI; reaches PyPI on the next
 prod deploy OR a manual `workflow_dispatch` on promote-prod.yml (with the tag to promote).
```

## First prod promote — migration note

Existing release tags (cut before `.spec-sha` was introduced) carry no `.spec-sha` file.
The per-sha resolver skips any tag without `.spec-sha`, so **the first prod dispatch will
abort with `::error::no released SDK matches`** — this is the correct fail-closed behaviour.

**How to bootstrap:** once a new `feat:` regen PR merges and release-please cuts a tag that
carries `.spec-sha`, the next prod dispatch will resolve that tag automatically.

To promote earlier (e.g. immediately after the first regen tag lands, without waiting for a
prod deploy), use the manual `workflow_dispatch` escape hatch, which skips the ancestry check:

```bash
gh workflow run promote-prod.yml --ref main -f tag=vX.Y.Z
```

This is intentional: the manual path is the human override for bootstrapping; the automated
path only promotes once a tag with a verified spec-commit record exists.

## ⚠️ PREREQ — PyPI Trusted Publisher (one-time, manual PyPI settings change)

The PyPI lane moved from `publish.yml` to **`promote-prod.yml`**. PyPI OIDC trusted
publishing matches on **repo + workflow filename + environment**, so the `onepin` project's
Trusted Publisher on pypi.org **must be updated** to:

- Workflow filename: **`promote-prod.yml`** (was `publish.yml`)
- Environment: **`pypi`**

Until that PyPI-side change lands, the `pypi` job's OIDC token mint will be rejected. This is
a manual settings change in the PyPI project — the workflow cannot self-configure it.
(TestPyPI's Trusted Publisher stays on `publish.yml` + environment `testpypi`.)

## Pre-mortem — how this ships the wrong thing, and what stops it

> Framing: *assume the pipeline already failed in production. What was the cause?*
> Each row is a concrete failure path with the control that prevents it.

| # | Failure (imagine it already happened) | Why it would happen | Mitigation (in place) |
|---|---|---|---|
| 1 | **Dynamic version ships `0.0.0`** to an index | A shallow/tagless checkout starves hatch-vcs of history, so it falls back to `0.0.0` | Every build job checks out `fetch-depth: 0` + `fetch-tags: true`; both lanes have a **fail-loud assert** on the *built* sdist version that rejects `0.0.0*` (and CI's `fresh-venv-smoke` asserts the same). The build aborts before any upload. |
| 2 | **Prod trigger missing / GitHub App absent** → customer release silently skipped | The `onepin-pipeline-bot` App / `PIPELINE_APP_ID`+`PIPELINE_APP_PRIVATE_KEY` secrets aren't set yet at a real prod deploy | `promote-prod.yml`'s gate warn-skips (`::warning::`) instead of failing, and emits a visible notice. **Replay:** once the App exists, run `promote-prod.yml` via `workflow_dispatch` with the tag. (The backend's `notify-sdk-repos` dispatch carries the same guard.) |
| 3 | **release-PR-merge gating** — "prod deployed but PyPI got nothing" | A regen `chore:` PR is invisible to release-please → no tag → nothing to promote | regen PRs are now **`feat:`** → release-please cuts a `vX.Y.Z` tag (`bump-minor-pre-major`). The promote iterates all `vX.Y.Z` tags newest-first; if none carry a valid `.spec-sha` ≤ S it aborts loudly (`::error::no released SDK matches`). |
| 4 | **`.devN` non-monotonic / collides on TestPyPI** | Two builds of the same commit, or out-of-order history, produce a stale/duplicate `.devN` | hatch-vcs derives `.devN` from **git distance** (monotonic with history under `fetch-depth: 0`); TestPyPI publish uses `skip-existing: true` so a genuine re-run/retag never breaks the chain. TestPyPI is internal-only — a non-monotonic dev number never reaches customers. |
| 5 | **Double-publish to the immutable PyPI index** | A re-dispatch / re-run / rollback re-fires the promote for an already-published version | `promote-prod.yml` **preflight**: `GET https://pypi.org/pypi/onepin/<version>/json`; HTTP `200` ⇒ `::error::` abort before upload. `concurrency: { group: promote-prod, cancel-in-progress: false }` serializes promotes. PyPI itself is the final backstop (rejects re-uploads). |
| 6 | **Wrong-version / wrong-sha promoted** to customers | Promote builds off a branch HEAD (a `.devN`), or promotes a tag whose API is ahead of the deployed spec | The build checks out `refs/tags/<resolved tag>` (qualified — never a same-named branch) and **asserts a clean `^[0-9]+\.[0-9]+\.[0-9]+$`** (a `.devN`/local aborts). **Per-sha pinning** (shipped): on a prod dispatch carrying spec commit S, the resolver iterates tags newest-first and promotes the newest tag whose `.spec-sha` is an ancestor-or-equal of S in the spec repo (`compare` base...head → `ahead`/`identical` = safe); any tag ahead of prod is skipped. Any API error during classification aborts the whole resolve (fail closed) — the immutable index is never touched with an uncertain result. |
| 7 | **Rollback re-dispatch republishes/downgrades** | A non-forward dispatch (e.g. a rollback) reaches the receiver | The PyPI lane only acts on `environment == 'prod'` dispatches; the immutable-index preflight (row 5) blocks a re-publish of an existing version. (The backend additionally gates `notify-sdk-repos` on `github.event_name == 'push'` so a rollback `workflow_dispatch` doesn't re-dispatch.) |

## Test plan (4 layers)

### 1. Unit
- **Version derivation / sanity assert** — `tests/build/` exercises a real `python -m build`
  and asserts the wheel/sdist version is sane (`test_dist_contents.py`); the lane asserts the
  same shape from the built sdist. Add a focused check that the `case 0.0.0*|*+*` reject and
  the `^[0-9]+\.[0-9]+\.[0-9]+$` clean-release regex behave (table of good/bad strings).
- **release-please config** — `release-please-validate.yml` runs the action in
  `skip-github-release + skip-github-pull-request` mode on any config/manifest change:
  this is a **config-sanity check only** (proves the `simple` config parses and computes
  a next version without writing source); it does **not** create a release PR or cut a tag,
  so it cannot serve as proof that a tag will be produced.
- **jq tag-resolver** — unit-check the `refs/tags → latest vX.Y.Z` filter (sub/test/select +
  `sort -V`) against a fixture tag list incl. the legacy `onepin-v0.2.0` (must be excluded).

### 2. Integration (single workflow, no customer mutation)
- **TestPyPI lane** — push to `main` touching `src/onepin/**`: confirm hatch-vcs stamps
  `X.Y.Z.devN`, the sanity assert passes, and the artifact lands on **TestPyPI** with
  `skip-existing`. Re-run to confirm `skip-existing` tolerates the collision.
- **PyPI lane gate** — `workflow_dispatch` `promote-prod.yml` **with no App secrets**: assert
  it `::warning::` warn-skips (no PyPI mutation). Dispatch a simulated `repository_dispatch`
  with `environment: dev`: assert it `::notice::` skips.
- **Preflight** — `workflow_dispatch` `promote-prod.yml` with `tag` = an **already-published**
  version: assert the preflight returns `200` and the job aborts with `::error::` *before* the
  `pypi` job.
- **actionlint** — `actionlint .github/workflows/*.yml` clean (CI-enforceable).

### 3. End-to-end (real release, gated on the App existing)
- Merge a `feat:` regen PR → release-please opens a release PR → merge it → tag `vX.Y.Z` →
  `publish.yml` fires → TestPyPI gets the clean `X.Y.Z`.
- Real backend **prod** deploy (`deploy-prod.yml`) → `repository_dispatch{environment:prod}`
  → `promote-prod.yml` resolves the tag, builds clean `X.Y.Z`, preflight passes, **PyPI**
  publish + provenance attestation. Verify `pip install onepin==X.Y.Z` from pypi.org and
  `onepin --version`.
- **Manual replay** path: `gh workflow run promote-prod.yml -f tag=vX.Y.Z` reaches PyPI
  identically (used when the App was absent at the original prod deploy).

### 4. Observability
- **Slack failure notifier** on both lanes (`notify-failure`, gated on `SLACK_WEBHOOK_URL`):
  fires on any build/publish failure with a direct run link. A clean warn-skip does **not**
  fire (skipped ≠ failed).
- **Build-provenance attestation** (PyPI lane, public-repo-gated): `actions/attest-build-provenance`
  + `gh attestation verify dist/*.whl --repo podonos/onepin-python` — a signed, verifiable
  record of exactly which commit/workflow produced the published bytes.
- **Traceability log** — the promote logs the dispatched `client_payload.sha` + `spec_version`
  and the resolved tag, so a published version can always be traced back to the prod deploy
  that triggered it.
- **PyPI preflight log** — the `GET …/json` HTTP code is echoed every run (visible proof the
  immutable-index guard ran).
