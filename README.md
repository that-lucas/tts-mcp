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
- A [Google Cloud project](https://console.cloud.google.com/freetrial) with the **Cloud Text-to-Speech API** enabled
  - Google offers a generous free tier — up to **4 million characters/month** for Standard/WaveNet voices and **1 million characters/month** for Neural2, Polyglot, and Chirp3 HD voices, more than enough for most individual use. See [TTS pricing](https://cloud.google.com/text-to-speech/pricing) for details.
- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) (`gcloud`) for authentication
- macOS uses `afplay` for playback by default (configurable via profile)

## Setup

### 1. Authenticate with Google Cloud

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

This stores credentials at `~/.config/gcloud/application_default_credentials.json`, which the TTS client discovers automatically. No environment variables needed.

### 2. Create a profiles file

```bash
tts-mcp --init
```

This creates a starter config at `~/.config/tts-mcp/profiles.json` with example profiles for every Google TTS voice tier. Edit it to pick your voice, format, and playback settings.

The server finds the profiles file automatically — no `--profiles` flag needed for the common case. The search order is:

1. `--profiles` flag or `GTTS_PROFILES` env var (explicit override)
2. `~/.config/tts-mcp/profiles.json` (XDG standard — created by `tts-mcp init`)
3. `./tts_profiles.json` (local dev fallback)

## MCP client setup

After running `tts-mcp init`, no `--profiles` flag is needed — the server finds `~/.config/tts-mcp/profiles.json` automatically. Just pass `--profile` to select which profile each client uses.

### Claude Code

```bash
claude mcp add --transport stdio --scope user \
  speech -- tts-mcp --profile claude_code
```

### OpenCode

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

### Codex CLI

Edit `~/.codex/config.toml`:

```toml
[mcp_servers.speech]
command = "tts-mcp"
args = ["--profile", "codex"]
```

### Using uvx (no global install)

Any client config can use `uvx` instead of installing globally:

```json
{
  "command": "uvx",
  "args": ["tts-mcp", "--profile", "opencode"]
}
```

## Usage

In any MCP-enabled client, prompt naturally:

- `Summarize this and read it aloud. use speech`
- `Stop current playback. use speech`

Tool names may appear prefixed by the client (e.g. `speech_tts_speak`, `speech_tts_stop`).

## CLI tools

The package also installs standalone CLI commands:

| Command          | Description                              |
| ---------------- | ---------------------------------------- |
| `tts-mcp`        | Start the MCP server                     |
| `tts-mcp --init` | Create starter config at `~/.config/tts-mcp/` |
| `tts-speak`      | Synthesize text to audio from the CLI    |
| `tts-voices`     | List available Google TTS voices         |
| `tts-batch`      | Generate samples for multiple voices     |

```bash
tts-mcp --init
tts-speak --text "Hello world" --voice en-US-Chirp3-HD-Fenrir --format wav --out hello.wav
tts-voices --language en-US --family Chirp3
tts-mcp --doctor --profile opencode
```

## Profile system

Profiles are defined in a JSON file (see [`profiles.example.json`](src/tts_mcp/profiles.example.json)):

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

- **Auth errors** — run `gcloud auth application-default login`, or confirm `GOOGLE_APPLICATION_CREDENTIALS` is set.
- **No audio** — verify the player binary (e.g. `afplay`) exists, or change `player_command` in your profile.
- **Tool timeout** — playback is non-blocking, but if timeouts persist, increase the client's `tool_timeout`.
- **Run diagnostics** — `tts-mcp --doctor` checks auth, profile, voice, and player.

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
