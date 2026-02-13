SHELL := /bin/bash

PYTHON ?= python3
VENV ?= .venv
RUN := $(VENV)/bin/python
PIP := $(RUN) -m pip

.PHONY: help setup test lint release

help:
	@echo "Targets:"
	@echo "  make setup   — create venv, install package in editable mode, set git hooks"
	@echo "  make test    — run pytest"
	@echo "  make lint    — run ruff check + format check"
	@echo "  make release — bump patch version, update pyproject.toml, tag, and push"

setup:
	@test -d "$(VENV)" || $(PYTHON) -m venv "$(VENV)"
	@$(PIP) install --quiet --upgrade pip
	@$(PIP) install --quiet -e ".[dev]"
	@git config core.hooksPath .githooks

test: setup
	@$(RUN) -m pytest

lint: setup
	@$(RUN) -m ruff check --output-format=concise .
	@$(RUN) -m ruff format --check .

release:
	@LAST_TAG=$$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0"); \
	MAJOR=$$(echo "$$LAST_TAG" | sed 's/^v//' | cut -d. -f1); \
	MINOR=$$(echo "$$LAST_TAG" | sed 's/^v//' | cut -d. -f2); \
	PATCH=$$(echo "$$LAST_TAG" | sed 's/^v//' | cut -d. -f3); \
	NEW_PATCH=$$((PATCH + 1)); \
	NEW_VERSION="$$MAJOR.$$MINOR.$$NEW_PATCH"; \
	NEW_TAG="v$$NEW_VERSION"; \
	echo "$$LAST_TAG → $$NEW_TAG"; \
	sed -i '' "s/^version = \".*\"/version = \"$$NEW_VERSION\"/" pyproject.toml; \
	git add pyproject.toml; \
	git commit -m "Bump version to $$NEW_VERSION"; \
	git tag "$$NEW_TAG"; \
	git push && git push origin "$$NEW_TAG"
