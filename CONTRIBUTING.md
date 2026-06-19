# Contributing to onepin

Thanks for your interest in improving the Onepin Python SDK + CLI.

## What lives here

This repository contains two distinct surfaces (see [AGENTS.md](./AGENTS.md) for detail):

- `src/onepin/` — **generated** SDK. Do not edit by hand; changes are overwritten when the SDK is regenerated from the OpenAPI spec.
- `src/onepin/_cli/` — the **hand-rolled** Typer CLI. This is where most contributions land.

If your change is to the generated SDK surface, it almost certainly belongs in the OpenAPI spec, not in this repo.

## Development setup

This project uses [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-extras   # or: make install
```

Common tasks:

```bash
make lint    # ruff check + format check (scoped to src/onepin/_cli + tests)
make test    # pytest
make build   # build wheel + sdist
```

When linting manually, always scope to the hand-rolled code — never run `ruff check .` (it skips `_cli/` due to the generated-tree exclude). Use:

```bash
uv run ruff check src/onepin/_cli tests
uv run ruff format src/onepin/_cli tests
```

## Tests

- Put tests under `tests/` (`unit/`, `cli/`, `build/`). Tests under `src/onepin/tests/` are not collected.
- `respx` mocks `httpx`; `pytest-asyncio` runs in auto mode.
- New behavior needs a test. Bug fixes need a regression test.
- PRs must keep diff coverage ≥ 90% and overall `onepin._cli` coverage ≥ 80%.

## Commit messages

Commits **must** follow [Conventional Commits](https://www.conventionalcommits.org/). This is enforced in CI (`commitlint`) and drives automated versioning and the changelog.

```
<type>: <summary>

[optional body]
```

Common types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`, `build`.

- `feat:` → minor release
- `fix:` → patch release
- `feat!:` or a `BREAKING CHANGE:` footer → breaking release

Do not hand-edit `CHANGELOG.md` or the version — release automation owns both.

## Pull requests

1. Branch from `main`.
2. Keep the change focused; one logical change per PR.
3. Ensure `make lint` and `make test` pass locally.
4. Open the PR against `main`. CI runs the full matrix (Python 3.10–3.13 on Linux, macOS, Windows) plus a fresh-venv install smoke test.
5. A maintainer review is required before merge. PRs squash-merge, so the PR title becomes the commit subject — make it a valid Conventional Commit.

## Reporting bugs and requesting features

Use the issue templates. For security issues, do **not** open a public issue — see [SECURITY.md](./SECURITY.md).

## License

By contributing, you agree that your contributions are licensed under the [MIT License](./LICENSE).
