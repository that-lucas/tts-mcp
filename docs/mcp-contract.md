# MCP Contract

This server is profile-driven: voice, language, model, format, output directory, and autoplay are fixed by profile configuration.

## Tools

### `tts_speak`

Generate speech from text with fixed profile settings.

Inputs:
- `text` (string, optional)
- `text_file` (string path, optional)
- `speaking_rate` (number, optional; defaults to profile value)
- `pitch` (number, optional; defaults to profile value)

Rules:
- Provide `text` or `text_file`.
- Do not provide both.

Output (success):
- `ok` (bool)
- `output_file` (string path)
- `mime_type` (string)
- `bytes` (int)
- `chars` (int)
- `played` (bool)
- `profile` (object with effective fixed settings)
- `usage` (object with month-to-date local usage counters)
- optional `playback_error`

Notes:
- Playback is launched in background mode (non-blocking) so tool calls can return immediately.

Output (failure):
- `ok=false`
- `error` (string)

### `tts_doctor`

Return runtime diagnostics for the active profile.

Output:
- `ok` (bool)
- `profile_file` (string)
- `profile_name` (string)
- `credentials_path` (string)
- `credentials_found` (bool)
- `profile_loaded` (bool)
- `client_ready` (bool)
- `voice_available` (bool)
- `player_available` (bool)
- `notes` (array of strings)
- optional `effective_profile`
- optional `error`

### `tts_stop`

Stop currently playing local audio for the configured playback command.

Output (success):
- `ok` (bool)
- `attempted` (bool)
- `player` (string)
- `stopped_processes` (int)

Output (failure):
- `ok=false`
- `error` (string)

## Intentional Restrictions

The MCP interface intentionally does not expose:
- voice selection
- language selection
- model selection
- output format selection

Those are configured per profile for each client/app.
