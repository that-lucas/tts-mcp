# Google Cloud TTS MCP Tooling

This is local tooling for Google Cloud Text-to-Speech.

Current scope is Google-specific. You can switch voices/models inside Google via profiles, but swapping providers (Groq/Azure/ElevenLabs/etc.) requires code changes.

It also includes an MCP server with profile-fixed output settings (voice/language/model/format), so model tools control text, speaking rate, and pitch.

## Fast path (single-command style)

From this folder, these are the only commands you need:

```bash
make setup
make oauth-login CLIENT_SECRET=~/Downloads/<oauth-client>.json PROJECT_ID=<gcp-project-id>
make speak TEXT="Hello Lucas. Speech is working." OUT=./out/hello.mp3
```

Then play it:

```bash
afplay ./out/hello.mp3
```

Optional health check:

```bash
make doctor
```

Run `make help` to see all available targets.

## MCP quickstart (OpenCode-first)

1) Confirm MCP runtime health:

```bash
make mcp-doctor MCP_PROFILE=opencode
```

2) Run MCP server (stdio transport):

```bash
make mcp-run MCP_PROFILE=opencode
```

3) In your MCP client config (OpenCode/Codex/Cloud Code), point to this command:

```bash
~/TTS/.venv/bin/python ~/TTS/mcp_server.py --profile-file ~/TTS/tts_profiles.json --profile opencode
```

The server tools are:
- `tts_speak` (inputs: `text|text_file`, `speaking_rate`, `pitch`)
- `tts_doctor`
- `tts_stop`

Note: `tts_speak` does not expose `voice/language/model/format` to the model. Those are fixed by profile (`tts_profiles.json`).

Playback behavior:
- auto-play in background + save
- tool response always includes `output_file`

Quick built-in test sentence:

```bash
make speak-test
afplay ./out/test-sentence.mp3
```

Use a specific voice for `speak-test`:

```bash
make speak-test VOICE=en-US-Chirp3-HD-Fenrir
make speak-test VOICE=en-US-Neural2-D
make speak-test VOICE=en-US-Chirp3-HD-Charon MODEL=models/chirp3-hd
```

Generate one file for every US voice across Chirp3 and Neural2:

```bash
make speak-us-all
```

This writes files into `./out` named as:

- `neural2-<voice>.mp3`
- `chirp3-<voice>.mp3`

Example: `chirp3-en-US-Chirp3-HD-Fenrir.mp3`

List voices (defaults to Chirp3 family):

```bash
make voices
make voices VOICES_LANGUAGE=en-US
make voices VOICES_LANGUAGE=en-US VOICE_FAMILY=Neural2
```

To test a specific model, pass `MODEL`:

```bash
make speak TEXT="Testing Chirp 3" MODEL=models/chirp3-hd OUT=./out/chirp3.mp3
```

If `MODEL` is not set, Google uses the default model behavior for the selected voice.

## 1) One-time Google Cloud setup

1. Create or choose a Google Cloud project.
2. Enable billing on that project.
3. Enable the Text-to-Speech API in that project.
4. Choose one auth method:
   - OAuth user login (recommended for personal trial)
   - Service account key (recommended for unattended automation)

## 2) OAuth method (your preferred option)

1. In Google Cloud Console, create an OAuth client:
   - `APIs & Services` -> `Credentials` -> `Create credentials` -> `OAuth client ID`
   - Application type: `Desktop app`
2. Download the OAuth client JSON file.
3. Generate a user credential file with refresh token:

```bash
cd ~/TTS
source .venv/bin/activate
python oauth_login.py \
  --client-secret-file "$HOME/Downloads/<oauth-client>.json" \
  --out "$HOME/.config/gcp/tts-oauth-user.json"
```

4. Export credentials path:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcp/tts-oauth-user.json"
```

If your app is in Testing mode, ensure your Google account is listed as a test user on the OAuth consent screen.

## 3) Service account method (optional alternative)

If you prefer service account auth later:

1. Create service account with role `Text-to-Speech User`.
2. Download JSON key.
3. Set:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcp/tts-sa.json"
```

## 4) Local install

```bash
cd ~/TTS
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 5) First synthesis test

```bash
cd ~/TTS
source .venv/bin/activate
python speak.py --text "Hello Lucas. This is your speech trial." --out ./out/hello.mp3
```

## 6) Useful variants

Makefile variants:

```bash
make speak TEXT="Testing another voice" VOICE=en-US-Chirp3-HD-Achird MODEL=models/chirp3-hd OUT=./out/achird.mp3
make speak TEXT="Neural2 test" VOICE=en-US-Neural2-D OUT=./out/neural2.mp3
make speak TEXT="Chirp 3 model test" VOICE=en-US-Chirp3-HD-Charon MODEL=models/chirp3-hd OUT=./out/chirp3.mp3
make speak TEXT="WAV output" FORMAT=wav OUT=./out/test.wav
make speak-ssml TEXT="<speak>Hello <break time='500ms'/> from SSML.</speak>" OUT=./out/ssml.mp3
```

Direct Python variants (equivalent):

Different Chirp3 voice:

```bash
python speak.py --text "Testing another Chirp3 voice" --voice en-US-Chirp3-HD-Achird --model models/chirp3-hd --out ./out/achird.mp3
```

WAV output:

```bash
python speak.py --text "WAV output test" --format wav --out ./out/test.wav
```

SSML input:

```bash
python speak.py --ssml --text "<speak>Hello <break time='500ms'/> from SSML.</speak>" --out ./out/ssml.mp3
```

## Notes on quota and cost

- The script writes local usage to `usage_log.csv`.
- It prints month-to-date character usage from `usage_log.csv`.
- This counter is local and does not replace actual Google billing reports.

## Profile configuration for MCP

Profiles live in:
- `tts_profiles.json` (active)
- `tts_profiles.example.json` (template)

Each profile fixes:
- `voice`
- `language`
- `model`
- `format`
- `output_dir`
- `usage_log`
- `autoplay`
- `player_command`

That means your MCP client can use one profile per app/client, while the model supplies text plus prosody (speaking rate and pitch).
