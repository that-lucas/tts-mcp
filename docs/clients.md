# Client Setup

This guide shows how to register this server in different MCP-capable clients.

Use absolute paths in all client configs.

## Shared values

- `REPO_DIR`: absolute path to this repository
- `CREDS_JSON`: absolute path to your Google credential file

Example:

```bash
REPO_DIR=/absolute/path/to/tts-mcp
CREDS_JSON=/absolute/path/to/tts-oauth-user.json
```

## OpenCode

Edit `~/.config/opencode/opencode.jsonc` and add:

```jsonc
{
  "mcp": {
    "speech": {
      "type": "local",
      "command": [
        "<REPO_DIR>/.venv/bin/python",
        "<REPO_DIR>/mcp_server.py",
        "--profile-file",
        "<REPO_DIR>/tts_profiles.json",
        "--profile",
        "opencode"
      ],
      "environment": {
        "GOOGLE_APPLICATION_CREDENTIALS": "<CREDS_JSON>"
      },
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

Edit `~/.codex/config.toml` and add:

```toml
[mcp_servers.speech]
command = "/absolute/path/to/tts-mcp/.venv/bin/python"
args = [
  "/absolute/path/to/tts-mcp/mcp_server.py",
  "--profile-file",
  "/absolute/path/to/tts-mcp/tts_profiles.json",
  "--profile",
  "codex"
]
env = { GOOGLE_APPLICATION_CREDENTIALS = "/absolute/path/to/tts-oauth-user.json" }
startup_timeout_sec = 15
tool_timeout_sec = 120
enabled = true
```

Verify:

```bash
codex mcp list
codex mcp get speech
```

## Claude Code CLI

Add the server:

```bash
claude mcp add --transport stdio --scope user \
  --env GOOGLE_APPLICATION_CREDENTIALS="<CREDS_JSON>" \
  speech -- \
  "<REPO_DIR>/.venv/bin/python" "<REPO_DIR>/mcp_server.py" \
  --profile-file "<REPO_DIR>/tts_profiles.json" \
  --profile claude_code
```

Verify:

```bash
claude mcp list
```

## Prompting tips

- Use hints like `use speech` when you want spoken output.
- Most clients prefix tool names with server name, so you may see:
  - `speech_tts_speak`
  - `speech_tts_doctor`
  - `speech_tts_stop`

## Troubleshooting

- If a client cannot connect after changes, restart that client session.
- Keep credentials explicit in MCP `env` for portability.
- Run `make mcp-doctor MCP_PROFILE=<profile>` to validate profile/auth/player readiness.
