# TTS MCP (Google Cloud Text-to-Speech)

Profile-driven MCP server and local CLI tools for Google Cloud Text-to-Speech.

This project is currently Google-specific. You can switch voices/models within Google through profiles, while keeping the same MCP tool interface.

## What this project provides

- MCP server with simple speech tools:
  - `tts_speak(text|text_file, speaking_rate, pitch)`
  - `tts_doctor()`
  - `tts_stop()`
- Profile-fixed runtime settings (not exposed to the model):
  - voice, language, model, format, output_dir, autoplay behavior
- Local CLI helpers for direct testing and voice exploration
- Non-blocking autoplay with local file persistence

## Quick start

```bash
git clone git@github.com:that-lucas/tts-mcp.git
cd tts-mcp
export ABS_PATH_TO_REPO="$(pwd)"

make setup
make doctor
```

## Requirements

- Python 3.11+
- Google Cloud project with billing enabled
- Google Cloud Text-to-Speech API enabled
- macOS playback uses `afplay` by default (configurable)

## Google Cloud account and authentication

### 1) Create and prepare your Google Cloud project

1. Create or choose a Google Cloud project.
2. Enable billing for that project.
3. Enable **Cloud Text-to-Speech API**.

### 2) Create OAuth credentials (recommended)

1. In Google Cloud Console, open `APIs & Services -> Credentials`.
2. Create `OAuth client ID`.
3. Choose application type `Desktop app`.
4. Download the OAuth client JSON file.

### 3) Generate user credentials for this project

```bash
cd "$ABS_PATH_TO_REPO"
source .venv/bin/activate

python oauth_login.py \
  --client-secret-file "<PATH_TO_OAUTH_CLIENT_JSON>" \
  --out "$HOME/.config/gcp/tts-oauth-user.json" \
  --quota-project "<GCP_PROJECT_ID>"
```

### 4) Set `GOOGLE_APPLICATION_CREDENTIALS`

You can set it in your shell profile (recommended), for example in Fish:

```fish
set --global --export GOOGLE_APPLICATION_CREDENTIALS "$HOME/.config/gcp/tts-oauth-user.json"
```

Or pass it explicitly in each MCP client config (recommended for portability/reliability).

## Local CLI usage

```bash
make help
make setup
make speak TEXT="Hello from Google TTS" OUT=./out/hello.wav FORMAT=wav
make voices VOICES_LANGUAGE=en-US VOICE_FAMILY=Chirp3
make speak-test VOICE=en-US-Chirp3-HD-Fenrir
```

## Profile system

Profiles are defined in:

- `tts_profiles.json` (active)
- `tts_profiles.example.json` (reference)

Each profile fixes:

- `voice`
- `language`
- `model`
- `format`
- `speaking_rate` (default used by MCP, still overridable per call)
- `pitch` (default used by MCP, still overridable per call)
- `output_dir`
- `usage_log`
- `autoplay`
- `player_command`

Current example profiles include `opencode`, `codex`, and `claude_code`.

## MCP server behavior

- Playback is launched in background mode (non-blocking).
- Output files are always saved.
- Default filename pattern:
  - `YYYY-MM-DD-HH-MM-SS-MMM.wav` (or `.mp3` / `.ogg`)

Run MCP diagnostics:

```bash
make mcp-doctor MCP_PROFILE=opencode
```

Run MCP server manually:

```bash
make mcp-run MCP_PROFILE=opencode
```

## Client setup

Use an absolute repository path in all client configs.

```bash
export ABS_PATH_TO_REPO="/absolute/path/to/tts-mcp"
export ABS_PATH_TO_CREDENTIALS_JSON="/absolute/path/to/tts-oauth-user.json"
```

### OpenCode

Edit `~/.config/opencode/opencode.jsonc`:

```jsonc
{
  "mcp": {
    "speech": {
      "type": "local",
      "command": [
        "<ABS_PATH_TO_REPO>/.venv/bin/python",
        "<ABS_PATH_TO_REPO>/mcp_server.py",
        "--profiles",
        "<ABS_PATH_TO_REPO>/tts_profiles.json",
        "--profile",
        "opencode"
      ],
      "environment": {
        "GOOGLE_APPLICATION_CREDENTIALS": "<ABS_PATH_TO_CREDENTIALS_JSON>"
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

### Codex CLI

Edit `~/.codex/config.toml`:

```toml
[mcp_servers.speech]
command = "<ABS_PATH_TO_REPO>/.venv/bin/python"
args = [
  "<ABS_PATH_TO_REPO>/mcp_server.py",
  "--profiles",
  "<ABS_PATH_TO_REPO>/tts_profiles.json",
  "--profile",
  "codex"
]
env = { GOOGLE_APPLICATION_CREDENTIALS = "<ABS_PATH_TO_CREDENTIALS_JSON>" }
startup_timeout_sec = 15
tool_timeout_sec = 120
enabled = true
```

Verify:

```bash
codex mcp list
codex mcp get speech
```

### Claude Code CLI

Add server:

```bash
claude mcp add --transport stdio --scope user \
  --env GOOGLE_APPLICATION_CREDENTIALS="<ABS_PATH_TO_CREDENTIALS_JSON>" \
  speech -- \
  "<ABS_PATH_TO_REPO>/.venv/bin/python" "<ABS_PATH_TO_REPO>/mcp_server.py" \
  --profiles "<ABS_PATH_TO_REPO>/tts_profiles.json" \
  --profile claude_code
```

Verify:

```bash
claude mcp list
```

## Using speech from prompts

In MCP-enabled clients, ask naturally and hint tool usage, for example:

- `Summarize this and read it aloud. use speech`
- `Stop current playback. use speech`

Depending on the client, tool names may appear prefixed (for example, `speech_tts_speak`, `speech_tts_stop`).

## Troubleshooting

- **MCP startup handshake fails (Codex):** ensure no stdout/stderr banner noise from server startup and verify command path points to project venv.
- **Tool timeout while audio plays:** this server uses non-blocking playback; if timeout persists, increase client `tool_timeout`.
- **No audio output:** verify player binary (`afplay`) exists, or change `player_command` in profile.
- **Auth errors:** confirm `GOOGLE_APPLICATION_CREDENTIALS` points to a valid JSON credential file.

## Security notes

- Do not commit credential files.
- Keep OAuth client secrets and authorized-user JSON files outside the repo.
- Review `.gitignore` before committing local artifacts.
