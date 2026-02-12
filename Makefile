SHELL := /bin/bash

PYTHON ?= python3
VENV ?= .venv
RUN := $(VENV)/bin/python
PIP := $(RUN) -m pip

.PHONY: help setup test lint

help:
	@echo "Targets:"
	@echo "  make setup  — create venv, install package in editable mode, set git hooks"
	@echo "  make test   — run pytest"
	@echo "  make lint   — run ruff check + format check"

setup:
	@test -d "$(VENV)" || $(PYTHON) -m venv "$(VENV)"
	@$(PIP) install --quiet -e ".[dev]"
	@git config core.hooksPath .githooks

test: setup
	@$(RUN) -m pytest

lint: setup
	@$(RUN) -m ruff check .
	@$(RUN) -m ruff format --check .
