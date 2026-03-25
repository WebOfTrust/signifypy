UV ?= uv
UV_ENV = UV_PROJECT_ENVIRONMENT=venv
UV_CACHE = UV_CACHE_DIR=$(CURDIR)/.uv-cache
INTEGRATION_POLL_INTERVAL ?= 0.1
INTEGRATION_HEAVY_POLL_INTERVAL ?= 0.25
INTEGRATION_PORT_POLL_INTERVAL ?= 0.1
INTEGRATION_WORKERS ?= 2
INTEGRATION_DIST ?= loadscope
INTEGRATION_TARGETS ?= tests/integration

.PHONY: help sync test test-fast test-ci test-integration test-integration-ci test-integration-parallel test-integration-parallel-ci build dist-check release-patch release-minor release-major release-bump docs clean guard-clean-worktree

help: ## Show available maintainer tasks
	@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z0-9_-]+:.*## / {printf "%-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

sync: ## Sync the local maintainer environment into ./venv
	@$(UV_CACHE) $(UV_ENV) $(UV) sync --group dev

test: ## Run the fast unit/contract suite
	@./venv/bin/python -m pytest -q $(PYTEST_ARGS) tests/app tests/core tests/peer

test-fast: test ## Alias for the fast test suite

test-ci: ## Run the fast suite with CI-friendly per-test output
	@./venv/bin/python -m pytest -vv $(PYTEST_ARGS) tests/app tests/core tests/peer

test-integration: ## Run the live integration suite
	@SIGNIFYPY_INTEGRATION_POLL_INTERVAL=$(INTEGRATION_POLL_INTERVAL) \
		SIGNIFYPY_INTEGRATION_HEAVY_POLL_INTERVAL=$(INTEGRATION_HEAVY_POLL_INTERVAL) \
		SIGNIFYPY_INTEGRATION_PORT_POLL_INTERVAL=$(INTEGRATION_PORT_POLL_INTERVAL) \
		./venv/bin/python -m pytest -q --run-integration $(PYTEST_ARGS) $(INTEGRATION_TARGETS)

test-integration-ci: ## Run integration tests with CI-friendly per-test output
	@SIGNIFYPY_INTEGRATION_POLL_INTERVAL=$(INTEGRATION_POLL_INTERVAL) \
		SIGNIFYPY_INTEGRATION_HEAVY_POLL_INTERVAL=$(INTEGRATION_HEAVY_POLL_INTERVAL) \
		SIGNIFYPY_INTEGRATION_PORT_POLL_INTERVAL=$(INTEGRATION_PORT_POLL_INTERVAL) \
		./venv/bin/python -m pytest -vv --run-integration $(PYTEST_ARGS) $(INTEGRATION_TARGETS)

test-integration-parallel: ## Run the live integration suite with a conservative xdist worker count
	@SIGNIFYPY_INTEGRATION_POLL_INTERVAL=$(INTEGRATION_POLL_INTERVAL) \
		SIGNIFYPY_INTEGRATION_HEAVY_POLL_INTERVAL=$(INTEGRATION_HEAVY_POLL_INTERVAL) \
		SIGNIFYPY_INTEGRATION_PORT_POLL_INTERVAL=$(INTEGRATION_PORT_POLL_INTERVAL) \
		./venv/bin/python -m pytest -q --run-integration -n $(INTEGRATION_WORKERS) --dist $(INTEGRATION_DIST) $(PYTEST_ARGS) $(INTEGRATION_TARGETS)

test-integration-parallel-ci: ## Run integration tests in parallel with CI-friendly per-test output
	@SIGNIFYPY_INTEGRATION_POLL_INTERVAL=$(INTEGRATION_POLL_INTERVAL) \
		SIGNIFYPY_INTEGRATION_HEAVY_POLL_INTERVAL=$(INTEGRATION_HEAVY_POLL_INTERVAL) \
		SIGNIFYPY_INTEGRATION_PORT_POLL_INTERVAL=$(INTEGRATION_PORT_POLL_INTERVAL) \
		./venv/bin/python -m pytest -vv --run-integration -n $(INTEGRATION_WORKERS) --dist $(INTEGRATION_DIST) $(PYTEST_ARGS) $(INTEGRATION_TARGETS)

build: ## Build source and wheel distributions
	@$(UV_CACHE) $(UV) build

dist-check: clean build ## Build release artifacts and validate them with twine
	@$(UV_CACHE) $(UV_ENV) $(UV) run --with twine twine check dist/*

release-patch: ## Prepare and commit a patch release
	@$(MAKE) release-bump BUMP=patch

release-minor: ## Prepare and commit a minor release
	@$(MAKE) release-bump BUMP=minor

release-major: ## Prepare and commit a major release
	@$(MAKE) release-bump BUMP=major

release-bump: guard-clean-worktree
	@VERSION_BEFORE=$$($(UV_CACHE) $(UV_ENV) $(UV) run python -c "import tomllib; from pathlib import Path; print(tomllib.load(Path('pyproject.toml').open('rb'))['project']['version'])"); \
	$(UV) version --bump $(BUMP); \
	VERSION_AFTER=$$($(UV_CACHE) $(UV_ENV) $(UV) run python -c "import tomllib; from pathlib import Path; print(tomllib.load(Path('pyproject.toml').open('rb'))['project']['version'])"); \
	echo "Preparing release $$VERSION_AFTER from $$VERSION_BEFORE"; \
	$(UV_CACHE) $(UV) lock; \
	$(UV_CACHE) $(UV_ENV) $(UV) run --group dev towncrier build --yes --version "$$VERSION_AFTER"; \
	git add -A pyproject.toml uv.lock docs/changelog.md newsfragments src/signify/__init__.py; \
	git commit -m "chore(release): $$VERSION_AFTER"

docs: ## Build the Sphinx documentation
	@./venv/bin/python -m sphinx -b html docs docs/_build/html

guard-clean-worktree:
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "Release preparation requires a clean git worktree."; \
		git status --short; \
		exit 1; \
	fi

clean: ## Remove build, docs, and test artifacts
	@rm -rf build dist docs/_build .pytest_cache .ruff_cache .uv-cache src/signifypy.egg-info
