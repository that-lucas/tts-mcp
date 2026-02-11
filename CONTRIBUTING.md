# Contributing

Thanks for your interest in contributing to tts-mcp.

## Prerequisites

- Python 3.11+
- A Google Cloud project with the Text-to-Speech API enabled
- Google Cloud CLI authenticated (`gcloud auth application-default login` — see README)

## Development setup

```bash
git clone git@github.com:that-lucas/tts-mcp.git
cd tts-mcp
make setup
pip install -e ".[dev]"
```

## Running tests

```bash
pytest
```

All Google API calls are mocked. No credentials are needed to run the test suite.

## Linting

```bash
ruff check .
ruff format --check .
```

To auto-fix issues:

```bash
ruff check --fix .
ruff format .
```

## How the profile system works

The MCP server is **profile-driven**. Voice, language, model, format, and output settings are fixed per profile and are **not exposed to the LLM**. Only `text`, `text_file`, `speaking_rate`, and `pitch` are controllable per tool call.

This is an intentional design decision for cost control and safety. If you are adding new MCP tool parameters, be careful not to expose settings that could lead to unexpected billing or voice changes.

## Pull requests

1. Fork the repo and create a feature branch.
2. Make your changes.
3. Ensure `pytest` and `ruff check .` pass.
4. Open a pull request against `main`.

Keep commits focused and write clear commit messages.
