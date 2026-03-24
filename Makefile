UV ?= uv
UV_ENV = UV_PROJECT_ENVIRONMENT=venv
UV_CACHE = UV_CACHE_DIR=$(CURDIR)/.uv-cache
INTEGRATION_POLL_INTERVAL ?= 0.1
INTEGRATION_HEAVY_POLL_INTERVAL ?= 0.25
INTEGRATION_PORT_POLL_INTERVAL ?= 0.1

.PHONY: help sync test test-fast test-ci test-integration test-integration-ci build release docs clean

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
		./venv/bin/python -m pytest -q --run-integration $(PYTEST_ARGS) tests/integration

test-integration-ci: ## Run integration tests with CI-friendly per-test output
	@SIGNIFYPY_INTEGRATION_POLL_INTERVAL=$(INTEGRATION_POLL_INTERVAL) \
		SIGNIFYPY_INTEGRATION_HEAVY_POLL_INTERVAL=$(INTEGRATION_HEAVY_POLL_INTERVAL) \
		SIGNIFYPY_INTEGRATION_PORT_POLL_INTERVAL=$(INTEGRATION_PORT_POLL_INTERVAL) \
		./venv/bin/python -m pytest -vv --run-integration $(PYTEST_ARGS) tests/integration

build: ## Build source and wheel distributions
	@$(UV_CACHE) $(UV) build

release: clean build ## Build release artifacts and validate them with twine
	@$(UV_CACHE) $(UV_ENV) $(UV) run --with twine twine check dist/*

docs: ## Build the Sphinx documentation
	@./venv/bin/python -m sphinx -b html docs docs/_build/html

clean: ## Remove build, docs, and test artifacts
	@rm -rf build dist docs/_build .pytest_cache .ruff_cache .uv-cache src/signifypy.egg-info
