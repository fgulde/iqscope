# List available recipes
default:
	just --list

# Install dependencies and set up git hooks
setup:
	uv sync --all-groups
	uv run pre-commit install

# Lint and check formatting
lint:
	uv run ruff check .
	uv run ruff format --check .

# Auto-fix lint findings and formatting
fmt:
	uv run ruff check --fix .
	uv run ruff format .

# Run the static type checker
typecheck:
	uv run mypy src tests

# Run the test suite
test:
	uv run pytest

# Run the test suite with an XML coverage report (for CI/Codecov)
coverage:
	uv run pytest --cov-report=xml

# Build the distributable package
build:
	uv build

# Tag the current commit as the next release (the tag is the version): just release patch|minor ["message"]
release part message="":
	uv run python scripts/release.py {{part}} "{{message}}"

# Run everything CI runs
check: lint typecheck test
