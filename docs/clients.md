# Client Setup

This guide shows how to register the tts-mcp server in different MCP clients.

## Prerequisites

1. Install: `pip install tts-mcp`
2. Have a `tts_profiles.json` file (copy from `tts_profiles.example.json`)
3. Authenticated via `gcloud auth application-default login` (see README for setup)

Replace `/path/to/tts_profiles.json` with your actual absolute path.

## Claude Code

```bash
claude mcp add --transport stdio --scope user \
  speech -- \
  tts-mcp --profiles /path/to/tts_profiles.json --profile claude_code
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
      "command": [
        "tts-mcp",
        "--profiles", "/path/to/tts_profiles.json",
        "--profile", "opencode"
      ],
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
args = [
  "--profiles", "/path/to/tts_profiles.json",
  "--profile", "codex"
]
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
  "args": ["tts-mcp", "--profiles", "/path/to/tts_profiles.json", "--profile", "opencode"]
}
```

## Prompting tips

- Use hints like `use speech` when you want spoken output.
- Most clients prefix tool names with the server name:
  - `speech_tts_speak`
  - `speech_tts_doctor`
  - `speech_tts_stop`

## Troubleshooting

- If a client cannot connect after changes, restart the client session.
- Run `gcloud auth application-default login` if auth fails.
- Run `tts-mcp --doctor --profiles /path/to/tts_profiles.json` to validate profile, auth, and player readiness.
