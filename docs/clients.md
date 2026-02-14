# Client Setup

This guide shows how to register the tts-mcp server in different MCP clients.

## Prerequisites

1. Install: `pip install tts-mcp`
2. Initialize profiles once: `tts-mcp --init` (creates `~/.config/tts-mcp/profiles.json`)
3. Customize profiles in that file (for example `claude`, `opencode`, `codex`)
4. Authenticate via `gcloud auth application-default login` (see README for setup)

`tts-mcp` auto-discovers profiles in this order:

1. `--profiles` flag (explicit override)
2. `TTS_MCP_PROFILES_PATH` env var
3. `~/.config/tts-mcp/profiles.json`

## Claude Code

```bash
claude mcp add --transport stdio --scope user \
  speech -- tts-mcp --profile claude
```

Verify:

```bash
claude mcp list
```

## OpenCode

Edit `~/.config/opencode/opencode.jsonc`:

```jsonc
{
  "mcp": {
    "speech": {
      "type": "local",
      "command": ["tts-mcp", "--profile", "opencode"],
      "enabled": true,
      "timeout": 120000
    }
  }
}
```

Verify:

```bash
opencode mcp list
```

## Codex CLI

Edit `~/.codex/config.toml`:

```toml
[mcp_servers.speech]
command = "tts-mcp"
args = ["--profile", "codex"]
startup_timeout_sec = 15
tool_timeout_sec = 120
enabled = true
```

Verify:

```bash
codex mcp list
codex mcp get speech
```

## Using uvx (no global install)

Any client can use `uvx` instead of a global pip install. Replace the command with:

```json
{
  "command": "uvx",
  "args": ["--update", "tts-mcp", "--profile", "opencode"]
}
```

## Optional: custom profile path

If you want profiles outside the default location, use one of:

- CLI flag: `tts-mcp --profiles /abs/path/profiles.json --profile opencode`
- Env var: `TTS_MCP_PROFILES_PATH=/abs/path/profiles.json`

You can also select a default profile via env var:

- `TTS_MCP_PROFILE_NAME=opencode`

## Prompting tips

- Hints like `use speech` are usually unnecessary, but they can help nudge the agent when it has access to many MCP servers.
- Most clients prefix tool names with the server name:
  - `speech_tts_speak`
  - `speech_tts_doctor`
  - `speech_tts_stop`

## Troubleshooting

- If a client cannot connect after changes, restart the client session.
- Run `gcloud auth application-default login` if auth fails.
- Run `tts-mcp --doctor` to validate profile, auth, voice, and player readiness.
