# RUNBOOK — onepin-python

Rollback and incident procedures per plan §F-ter.5.

## Bad SDK on PyPI

Use `twine yank` (PEP 592). Yanked versions are skipped for new installs but still reachable by pinned requirements. NEVER use `twine delete` — PyPI deletion is irrevocable.

```bash
# Yank a broken release
twine yank onepin==0.1.3 --reason "broken upload flow — install 0.1.4 instead"

# Unyank if the concern was a false alarm
twine unyank onepin==0.1.3
```

## Bad tag (not yet on PyPI)

Only viable before `publish.yml` completes. After PyPI upload, use yank instead.

```bash
git tag -d v0.X.Y
git push --delete origin v0.X.Y
```

## Bad release-please PR

Close the PR. The bot recreates it on the next push to main with a rebased state.

## Compromised `ONEPIN_DEV_API_KEY`

1. Rotate via [app.onepin.ai/settings/api-keys](https://app.onepin.ai/settings/api-keys)
2. Update the `ONEPIN_DEV_API_KEY` GitHub organization secret
3. Re-run any failed live-smoke jobs

## Compromised `SLACK_WEBHOOK_ONEPIN_SDK`

1. Regenerate in Slack app settings
2. Update the `SLACK_WEBHOOK_ONEPIN_SDK` GitHub organization secret

## Fern auto-PR introduced a regression

Revert the merged Fern PR on `onepin-python`. The next event-driven Fern regen (triggered by the next spec-sync merge in `onepin-sdks`) will produce a fresh PR with the corrected SDK.

## Docs site is broken

1. Quick fix: In Cloudflare Pages dashboard → onepin-sdks project → Deployments → click "Rollback to this deployment" on last known-good deploy.
2. Permanent fix: Revert the bad markdown commit on `onepin-sdks` main → Cloudflare Pages auto-rebuilds.

## CI pipeline is stuck

Alert channel: **#alert-onepin-sdk**

All CI/release/docs failures across donut-be webhook, onepin-sdks, and onepin-python route here. Check the linked action run URL in the Slack message.
