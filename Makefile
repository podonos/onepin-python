.PHONY: install lint typecheck test build publish-test help

help:
	@echo "Targets: install lint typecheck test build publish-test"

install:
	uv sync --all-extras

lint:
	uv run ruff check src/onepin/_cli tests && uv run ruff format --check src/onepin/_cli tests

typecheck:
	uv run mypy -p onepin._cli

test:
	uv run pytest -q

build:
	uv run python -m build

publish-test:
	uv run twine upload --repository testpypi dist/*
