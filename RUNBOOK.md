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

Only viable before `publish.yml` completes. After PyPI upload, use `twine yank`
instead.

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
- TestPyPI / PyPI upload error → inspect the publish job logs and re-trigger.
- Attestation verification failure → confirm the `--repo` flag is scoped
  correctly in `publish.yml`.

## Publishing a release

Merging the release-please PR tags the version; `publish.yml` then builds → TestPyPI →
PyPI (OIDC trusted publishing). Auto-publish on release requires the **`RELEASE_PAT`**
repo secret. release-please uses this token for **all** its GitHub calls, so it needs both
`contents: write` (to push the tag, which fires `publish.yml`'s `push: tags` trigger) **and**
`pull requests: write` (to create/update the release PR) — a `contents`-only PAT fails the
next release-please run before any tag is cut. Without the secret nothing publishes;
release-please falls back to the default token. Use a fine-grained PAT scoped to
`podonos/onepin-python` only, with an expiry; rotation is tracked in the private ops runbook.

Manual fallback (publish an existing tag):

```bash
# Run on the tag ref, not the default branch, or the version resolves wrong.
gh workflow run publish.yml --ref vX.Y.Z -f tag=vX.Y.Z
```
