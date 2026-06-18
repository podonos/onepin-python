// Commitlint configuration.
//
// Migrated from .commitlintrc.json so we can use a function-based `ignores`
// rule (not expressible in JSON). Dependabot's default commit subject for some
// updates is `Bump <dep> from <x> to <y>` with no Conventional Commits type
// prefix — this happens for indirect/transitive dependencies even when
// .github/dependabot.yml sets `commit-message.prefix`. Ignore that format so
// those automated PRs don't fail the commitlint check.
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'body-max-line-length': [2, 'always', 120],
  },
  // `ignores` is additive: built-in defaultIgnores (merge/revert/fixup/squash)
  // still apply. Kept explicit so the additive-vs-replace semantics are obvious.
  defaultIgnores: true,
  ignores: [(message) => /^Bump .+ from .+ to .+/i.test(message)],
};
