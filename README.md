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

1. `--profiles` flag or `TTS_MCP_PROFILES_PATH` env var (explicit override)
2. `~/.config/tts-mcp/profiles.json` (XDG standard — created by `tts-mcp --init`)
3. `./tts_profiles.json` (local dev fallback)

## MCP client setup

After running `tts-mcp --init`, no `--profiles` flag is needed — the server finds `~/.config/tts-mcp/profiles.json` automatically. Just pass `--profile` to select which profile each client uses.

### Claude Code

```bash
claude mcp add --transport stdio --scope user \
  speech -- tts-mcp --profile claude
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

## CLI reference

The package installs four commands. Each supports `--help` for full details.

### `tts-mcp` — MCP server and management

```bash
tts-mcp --init              # create starter config at ~/.config/tts-mcp/profiles.json
tts-mcp --init --force      # overwrite existing config
tts-mcp --doctor            # diagnostics: auth, profile, voice, player
tts-mcp --profile casual    # start MCP server with a specific profile
```

Defaults:

- `--profiles`: `TTS_MCP_PROFILES_PATH` env var or `""` (then auto-discovery runs)
- `--profile`: `TTS_MCP_PROFILE_NAME` env var or `""` (then `default_profile` is used)
- `--doctor`, `--init`, `--force`: `false`

### `tts-speak` — synthesize text to audio

```bash
tts-speak --text "Hello world" --voice en-US-Chirp3-HD-Fenrir --format wav --out hello.wav
tts-speak --text-file notes.txt --voice en-US-Neural2-D --format mp3 --out notes.mp3
tts-speak --ssml --text "<speak>Hello <break time='500ms'/> world</speak>" --out ssml.wav
echo "Piped text" | tts-speak --voice en-US-Casual-K --out piped.ogg
```

Options: `--text`, `--text-file`, `--voice`, `--language`, `--model`, `--format` (mp3/ogg/wav), `--speaking-rate`, `--pitch`, `--out`, `--usage-log`.

Defaults:

- `--voice`: `""`
- `--language`: `en-US`
- `--model`: `""`
- `--format`: `mp3`
- `--speaking-rate`: `1.0`
- `--pitch`: `0.0`
- `--out`: `""` (auto-generates a timestamped filename in the current directory)
- `--usage-log`: `usage_log.csv`
- input: if neither `--text` nor `--text-file` is provided, the CLI prompts for text

### `tts-voices` — list available voices

```bash
tts-voices                              # list en-US voices (default language)
tts-voices --language en-US             # filter by language
tts-voices --language en-US --family Chirp3   # filter by family
tts-voices --limit 5                    # limit results
```

Defaults:

- `--language`: `en-US`
- `--family`: `""` (no family filter)
- `--limit`: `0` (no limit)

### `tts-batch` — generate samples for multiple voices

```bash
tts-batch --text-file test.txt --out-dir ./samples
tts-batch --text-file test.txt --families Chirp3,Neural2 --language en-US --format wav
tts-batch --text-file test.txt --limit 3   # first 3 matching voices only
```

Defaults:

- `--families`: `""` (no family filter)
- `--language`: `en-US`
- `--format`: `mp3`
- `--out-dir`: `./out`
- `--speaking-rate`: `1.0`
- `--pitch`: `0.0`
- `--limit`: `0` (all matching voices)
- `--text-file`: required

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
      "output_dir": "~/.local/share/tts-mcp/out",
      "usage_log": "~/.local/share/tts-mcp/usage_log.csv",
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
make setup    # creates venv, installs package + dev deps, sets git hooks
make test     # run pytest
make lint     # run ruff check + format check
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT
