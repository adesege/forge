# forge — Makefile
# Primary interface for development tasks.
# Proxies to uv, pytest, podman, and helm.

-include .env
export



PYTHON ?= uv run python
PYTEST ?= uv run pytest

BEHAVE ?= uv run behave


.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Python / uv ──────────────────────────────────────────────

.PHONY: install
install: ## Install project dependencies
	uv sync

.PHONY: install-dev
install-dev: ## Install with dev dependencies
	uv sync --all-groups

.PHONY: lint
lint: ## Run linting (ruff + mypy)
	uv run ruff check src/ tests/
	uv run mypy src/

.PHONY: format
format: ## Format code with ruff
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

.PHONY: test
test: ## Run all tests
	$(PYTEST) tests/ -v

.PHONY: test-unit
test-unit: ## Run unit tests only
	$(PYTEST) tests/unit -v


.PHONY: test-bdd
test-bdd: ## Run BDD/Gherkin feature tests
	$(BEHAVE) features/

.PHONY: test-all
test-all: test test-bdd ## Run unit + BDD tests


.PHONY: coverage
coverage: ## Generate test coverage report
	$(PYTEST) tests/ --cov=src/forge --cov-report=html --cov-report=term
	@echo "Coverage report: htmlcov/index.html"

.PHONY: run
run: ## Run the CLI
	uv run forge --help



.PHONY: demo
demo: ## Record an asciinema demo
	uv run asciinema rec --command "uv run forge --help" demo.cast


# ── Documentation ────────────────────────────────────────────

.PHONY: docs
docs: ## Build Sphinx documentation
	cd docs && uv run make html

.PHONY: serve-docs
serve-docs: ## Serve docs locally
	$(PYTHON) -m http.server 8000 --directory docs/_build/html







# ── Debian package ──────────────────────────────────────────

VERSION ?= $(shell grep '^version' pyproject.toml | head -1 | sed 's/.*"\(.*\)"/\1/')
DEB_NAME ?= forge
DEB_PKG_DIR = dist/$(DEB_NAME)_$(VERSION)

.PHONY: build-deb
build-deb: build ## Build Debian package from wheel
	rm -rf $(DEB_PKG_DIR)
	mkdir -p $(DEB_PKG_DIR)/DEBIAN
	mkdir -p $(DEB_PKG_DIR)/opt/$(DEB_NAME)
	mkdir -p $(DEB_PKG_DIR)/usr/bin
	printf 'Package: $(DEB_NAME)\nVersion: $(VERSION)\nSection: utils\nPriority: optional\nArchitecture: all\nDepends: python3 (>= 3.14.0)\nMaintainer: Brian Payne\nDescription: forge — a click-clop project\n' \
		> $(DEB_PKG_DIR)/DEBIAN/control
	cp dist/*.whl $(DEB_PKG_DIR)/opt/$(DEB_NAME)/
	printf '#!/bin/sh\npip3 install --force-reinstall /opt/$(DEB_NAME)/*.whl\n' \
		> $(DEB_PKG_DIR)/DEBIAN/postinst
	chmod 755 $(DEB_PKG_DIR)/DEBIAN/postinst
	dpkg-deb --build $(DEB_PKG_DIR) dist/$(DEB_NAME)_$(VERSION)_all.deb



# ── Publishing ──────────────────────────────────────────────

FORGEJO_HOST ?= git.app.home.southroute.com
PACKAGE_OWNER ?= bayne


FORGEJO_TOKEN ?= dcaf3a0766e9b9ff42d7461e9d415045c61dc266



.PHONY: publish-pypi
publish-pypi: build ## Publish to Forgejo PyPI registry
	uv publish \
		--publish-url "https://$(FORGEJO_HOST)/api/packages/$(PACKAGE_OWNER)/pypi" \
		--token "$(FORGEJO_TOKEN)"




.PHONY: publish-deb
publish-deb: build-deb ## Upload Debian package to Forgejo registry
	@DEB_FILE=$$(ls dist/*.deb | head -1) && \
	curl --fail -X PUT \
		-H "Authorization: token $(FORGEJO_TOKEN)" \
		-H "Content-Type: application/octet-stream" \
		--upload-file "$${DEB_FILE}" \
		"https://$(FORGEJO_HOST)/api/packages/$(PACKAGE_OWNER)/debian/pool/trixie/main/upload"


.PHONY: publish-all
publish-all: publish-pypi publish-deb ## Publish all artifacts


# ── Release ─────────────────────────────────────────────────

BUMP ?= patch
RELEASE_BRANCH ?= main

.PHONY: release
release: ## Bump version, tag, and publish all artifacts (BUMP=patch|minor|major)
	@BRANCH=$$(git rev-parse --abbrev-ref HEAD); \
	if [ "$$BRANCH" != "$(RELEASE_BRANCH)" ]; then \
		echo "Error: releases must be from $(RELEASE_BRANCH) (currently on $$BRANCH)"; \
		exit 1; \
	fi
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "Error: working tree is not clean — commit or stash first"; \
		exit 1; \
	fi
	@CURRENT=$$(grep '^version' pyproject.toml | head -1 | sed 's/.*"\(.*\)"/\1/'); \
	IFS='.' read -r MAJOR MINOR PATCH <<< "$$CURRENT"; \
	case "$(BUMP)" in \
		major) MAJOR=$$((MAJOR + 1)); MINOR=0; PATCH=0;; \
		minor) MINOR=$$((MINOR + 1)); PATCH=0;; \
		patch) PATCH=$$((PATCH + 1));; \
		*) echo "Error: BUMP must be patch, minor, or major"; exit 1;; \
	esac; \
	NEW="$$MAJOR.$$MINOR.$$PATCH"; \
	sed -i "s/^version = \".*\"/version = \"$$NEW\"/" pyproject.toml; \
	echo "$$CURRENT → $$NEW"; \
	git add pyproject.toml; \
	git commit -m "release: v$$NEW"; \
	git tag -a "v$$NEW" -m "Release v$$NEW"

	$(MAKE) publish-all

	git push origin $(RELEASE_BRANCH) --tags

# ── Git hooks ────────────────────────────────────────────────

.PHONY: hooks
hooks: ## Install git hooks
	git config core.hooksPath .git-hooks
	@echo "Git hooks installed from .git-hooks/"

# ── Cleanup ──────────────────────────────────────────────────

.PHONY: clean
clean: ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info .coverage htmlcov/

.PHONY: build
build: clean ## Build distribution package
	uv build
