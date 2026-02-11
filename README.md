# tts-mcp

Profile-driven MCP server for Google Cloud Text-to-Speech.

Exposes three tools to any MCP client:

- **`tts_speak`** — synthesize text to audio and auto-play it
- **`tts_doctor`** — run diagnostics on auth, profile, and playback
- **`tts_stop`** — stop any currently playing audio

Voice, language, model, and format are locked per profile — the LLM can only control text content, speaking rate, and pitch.

## Install

```bash
pip install tts-mcp
```

Or with [uvx](https://docs.astral.sh/uv/) (no install needed):

```bash
uvx tts-mcp --help
```

## Prerequisites

- Python 3.11+
- A Google Cloud project with billing and the **Cloud Text-to-Speech API** enabled
- Google OAuth or service account credentials
- macOS uses `afplay` for playback by default (configurable via profile)

## Setup

### 1. Create Google Cloud credentials

1. In Google Cloud Console, go to **APIs & Services > Credentials**.
2. Create an **OAuth client ID** (Desktop app) and download the JSON file.
3. Generate user credentials:

```bash
tts-oauth \
  --client-secret-file ~/Downloads/client_secret.json \
  --out ~/.config/gcp/tts-oauth-user.json \
  --quota-project YOUR_PROJECT_ID
```

### 2. Create a profiles file

Copy the example and customize:

```bash
cp tts_profiles.example.json tts_profiles.json
```

Each profile fixes voice, language, model, format, output directory, and playback settings. See [`tts_profiles.example.json`](tts_profiles.example.json) for the full schema.

### 3. Set credentials

Either export globally:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcp/tts-oauth-user.json"
```

Or pass explicitly per MCP client config (recommended).

## MCP client setup

### Claude Code

```bash
claude mcp add --transport stdio --scope user \
  --env GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcp/tts-oauth-user.json" \
  speech -- \
  tts-mcp --profiles /path/to/tts_profiles.json --profile claude_code
```

### OpenCode

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
      "environment": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/tts-oauth-user.json"
      },
      "enabled": true,
      "timeout": 120000
    }
  }
}
```

### Codex CLI

Edit `~/.codex/config.toml`:

```toml
[mcp_servers.speech]
command = "tts-mcp"
args = [
  "--profiles", "/path/to/tts_profiles.json",
  "--profile", "codex"
]
env = { GOOGLE_APPLICATION_CREDENTIALS = "/path/to/tts-oauth-user.json" }
```

### Using uvx (no global install)

Any client config can use `uvx` instead of installing globally:

```json
{
  "command": "uvx",
  "args": ["tts-mcp", "--profiles", "/path/to/tts_profiles.json", "--profile", "opencode"]
}
```

## Usage

In any MCP-enabled client, prompt naturally:

- `Summarize this and read it aloud. use speech`
- `Stop current playback. use speech`

Tool names may appear prefixed by the client (e.g. `speech_tts_speak`, `speech_tts_stop`).

## CLI tools

The package also installs standalone CLI commands:

| Command      | Description                              |
| ------------ | ---------------------------------------- |
| `tts-mcp`    | Start the MCP server                     |
| `tts-speak`  | Synthesize text to audio from the CLI    |
| `tts-voices` | List available Google TTS voices         |
| `tts-batch`  | Generate samples for multiple voices     |
| `tts-oauth`  | Run the OAuth credential setup flow      |

```bash
tts-speak --text "Hello world" --voice en-US-Chirp3-HD-Fenrir --format wav --out hello.wav
tts-voices --language en-US --family Chirp3
tts-mcp --doctor --profiles tts_profiles.json --profile opencode
```

## Profile system

Profiles are defined in a JSON file (see [`tts_profiles.example.json`](tts_profiles.example.json)):

```json
{
  "default_profile": "opencode",
  "profiles": {
    "opencode": {
      "voice": "en-US-Chirp3-HD-Fenrir",
      "language": "en-US",
      "model": "models/chirp3-hd",
      "format": "wav",
      "speaking_rate": 1.0,
      "pitch": 0.0,
      "output_dir": "./out",
      "usage_log": "./usage_log.csv",
      "autoplay": true,
      "player_command": ["afplay", "{file}"]
    }
  }
}
```

Each profile locks: `voice`, `language`, `model`, `format`, `output_dir`, `usage_log`, `autoplay`, and `player_command`. Only `speaking_rate` and `pitch` can be overridden per tool call.

## Troubleshooting

- **Auth errors** — confirm `GOOGLE_APPLICATION_CREDENTIALS` points to a valid credential file.
- **No audio** — verify the player binary (e.g. `afplay`) exists, or change `player_command` in your profile.
- **Tool timeout** — playback is non-blocking, but if timeouts persist, increase the client's `tool_timeout`.
- **Run diagnostics** — `tts-mcp --doctor --profiles tts_profiles.json` checks auth, profile, voice, and player.

## Development

```bash
git clone git@github.com:that-lucas/tts-mcp.git
cd tts-mcp
make setup
pip install -e ".[dev]"
pytest
ruff check .
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT
