# Client Setup Notes

## OpenCode (primary)

Add an MCP server entry that starts `mcp_server.py` over stdio.

Suggested OpenCode config snippet:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "speech": {
      "type": "local",
      "command": [
        "/ABS/PATH/TO/TTS/.venv/bin/python",
        "/ABS/PATH/TO/TTS/mcp_server.py",
        "--profile-file",
        "/ABS/PATH/TO/TTS/tts_profiles.json",
        "--profile",
        "opencode"
      ],
      "environment": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/ABS/PATH/TO/tts-oauth-user.json"
      },
      "enabled": true
    }
  }
}
```

Equivalent command:

```bash
~/TTS/.venv/bin/python ~/TTS/mcp_server.py --profile-file ~/TTS/tts_profiles.json --profile opencode
```

Required env var:

```bash
GOOGLE_APPLICATION_CREDENTIALS=$HOME/.config/gcp/tts-oauth-user.json
```

Prompting tip in OpenCode:
- Add guidance in your agent instructions: "When user asks for spoken output, call `tts_speak`."
- Add `use speech` in prompts to strongly bias OpenCode toward that MCP server.
- OpenCode prefixes MCP tools with server name, so this appears as `speech_tts_speak`, `speech_tts_doctor`, and `speech_tts_stop`.

## Codex CLI (secondary)

Use the same stdio server command and env var as OpenCode. Register the server in Codex MCP config using a local command transport.

## Cloud Code (secondary)

Use the same stdio command and credentials env var. Register as a local MCP tool server.

## GitHub CLI (later)

Treat as follow-up integration. MCP patterns in GitHub CLI workflows are less standardized than OpenCode/Codex-style MCP clients.
