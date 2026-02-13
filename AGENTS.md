# AGENTS.md
Guidance for coding agents operating in this repository.

## Repository Overview
- Project: `tts-mcp`
- Language: Python 3.11+
- Packaging: Hatchling (`pyproject.toml`)
- Source root: `src/tts_mcp/`
- Tests root: `tests/`
- Runtime modes: MCP server (`tts-mcp`) + CLIs (`tts-speak`, `tts-voices`, `tts-batch`)

## Key Modules
- `src/tts_mcp/server.py` - MCP entrypoint and tool registration
- `src/tts_mcp/speak.py` - local synthesis CLI
- `src/tts_mcp/list_voices.py` - voice listing CLI
- `src/tts_mcp/batch.py` - multi-voice generation CLI
- `src/tts_mcp/core/auth.py` - Google ADC client creation
- `src/tts_mcp/core/profile.py` - profile resolution/load/playback
- `src/tts_mcp/core/synth.py` - synthesis helpers and request/result models
- `src/tts_mcp/core/voices.py` - voice filtering
- `src/tts_mcp/core/usage.py` - usage/cost snapshot logic
- `README.md` and `CONTRIBUTING.md` - user/developer docs

## Canonical Dev Commands
Use Make targets first:

```bash
make setup
make test
make lint
make lint-fix
```

What they do:
- `make setup`: create `.venv`, install editable package + dev deps, set git hooks
- `make test`: run pytest via `.venv/bin/python -m pytest`
- `make lint`: run `ruff check --output-format=concise .` and `ruff format --check .`
- `make lint-fix`: auto-fix lint issues and apply formatting

## Code Style Guidelines

### Imports
- Group and sort imports: stdlib, third-party, local
- Follow Ruff isort behavior; do not hand-format against it
- No wildcard imports; remove unused imports

### Formatting
- Line length is 120
- Use double quotes (Ruff formatter default)
- Let Ruff handle spacing/wrapping

### Types
- Prefer explicit type annotations for params and returns
- Keep `from __future__ import annotations` (existing project pattern)
- Use built-in generics (`list[str]`, `dict[str, Any]`, etc.)
- Use dataclasses for structured transfer objects

### Naming
- `snake_case`: functions, vars, modules
- `PascalCase`: classes/dataclasses
- `UPPER_SNAKE_CASE`: constants
- Tests named `test_<behavior>`

### Architecture Boundaries
- Keep command modules orchestration-focused
- Put reusable logic in `src/tts_mcp/core/`
- Keep dependency direction one-way: CLI/server -> core
- Avoid cross-module leakage of CLI concerns into core

### Paths and Filesystem
- Use `pathlib.Path`
- Resolve user paths with `.expanduser().resolve()` where appropriate
- Ensure output parent dirs exist before writes

### Error Handling
- Core modules: raise `ValueError` for invalid input/state
- Core modules: raise `RuntimeError` for runtime/environment failures
- CLI entrypoints: convert expected failures to `SystemExit` with clear messages
- MCP tools: return structured errors like `{"ok": false, "error": "..."}`
- Avoid exposing stack traces for expected user errors

### Output and UX
- CLI status output intentionally uses `print()`
- Keep outputs concise and stable
- Avoid adding noisy debug prints in normal paths

### Documentation Discipline
- Update `README.md` when changing CLI flags/defaults/env vars/tool behavior
- Keep docs aligned with actual defaults shown in `--help`
- Current profile env vars are:
  - `TTS_MCP_PROFILES_PATH`
  - `TTS_MCP_PROFILE_NAME`

## Testing Expectations for Code Changes
- Add/update tests for every behavior change
- Prefer focused unit tests with mocks for Google APIs and subprocess
- Parser/default/help changes should update `tests/test_*_cli.py`
- Core logic changes should update `tests/core/test_*.py`
- Tests should always be run via `make test` (do not use direct `pytest` commands in normal workflow)
- Before PRs, run both:

```bash
make test
make lint
```

## Product Constraints to Preserve
- MCP tools are `tts_speak`, `tts_doctor`, `tts_stop`
- MCP is intentionally profile-driven for voice/language/model/format
- Be careful when exposing new MCP params; avoid billing/voice drift surprises

## Git and Artifact Hygiene
- Keep commits focused; avoid unrelated refactors
- Do not commit generated audio, logs, caches, or `.venv`
- Respect existing lint/test gates before pushing

## Development Workflow (Required)
- Never commit directly to `main`
- Always create a feature/fix branch before making commits
- Push branch and open a PR for every code change
- Treat PR creation as the review gate; wait for review feedback before merge
- After opening a PR, check review comments and address them in follow-up commits on the same branch
- Re-run relevant tests/lint after addressing review feedback
