#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import shutil
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.utilities.logging import configure_logging

from tts_core.auth import create_tts_client
from tts_core.profile import TTSProfile, load_profile, play_audio, stop_audio
from tts_core.synth import SynthesisRequest, read_text_input, synthesize_to_file, timestamped_output_path
from tts_core.usage import append_usage_row, create_usage_snapshot
from tts_core.voices import list_voices

PROFILES_ENV = "GTTS_PROFILES"
PROFILE_NAME_ENV = "GTTS_PROFILE"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Google TTS MCP server")
    parser.add_argument(
        "--profiles",
        default=os.getenv(PROFILES_ENV, "./tts_profiles.json"),
        help="Path to TTS profile JSON file.",
    )
    parser.add_argument(
        "--profile",
        default=os.getenv(PROFILE_NAME_ENV, ""),
        help="Profile name to use. Falls back to default_profile in JSON.",
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Print diagnostics JSON and exit without starting MCP server.",
    )
    return parser.parse_args()


def load_runtime(profile_file: str, profile_name: str) -> tuple[TTSProfile, Any]:
    profile = load_profile(Path(profile_file), profile_name)
    client = create_tts_client()
    return profile, client


def doctor_report(profile_file: str, profile_name: str) -> dict[str, Any]:
    report: dict[str, Any] = {
        "ok": True,
        "profile_file": str(Path(profile_file).expanduser().resolve()),
        "profile_name": profile_name or "<default>",
        "credentials_path": os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
        "credentials_found": False,
        "profile_loaded": False,
        "client_ready": False,
        "voice_available": False,
        "player_available": False,
        "notes": [],
    }

    creds = report["credentials_path"]
    if creds:
        report["credentials_found"] = Path(creds).expanduser().exists()

    try:
        profile, client = load_runtime(profile_file, profile_name)
        report["profile_loaded"] = True
        report["client_ready"] = True
        report["effective_profile"] = {
            "name": profile.name,
            "voice": profile.voice,
            "language": profile.language,
            "model": profile.model,
            "format": profile.audio_format,
            "speaking_rate": profile.speaking_rate,
            "pitch": profile.pitch,
            "output_dir": str(profile.output_dir),
            "usage_log": str(profile.usage_log),
            "autoplay": profile.autoplay,
            "player_command": profile.player_command,
        }

        voices = list_voices(client, language=profile.language, family="", limit=0)
        report["voice_available"] = any(item.name == profile.voice for item in voices)

        if profile.autoplay and profile.player_command:
            player_bin = profile.player_command[0]
            report["player_available"] = shutil.which(player_bin) is not None
            if not report["player_available"]:
                report["notes"].append(f"Audio player not found: {player_bin}")
        else:
            report["player_available"] = True
    except Exception as exc:  # noqa: BLE001
        report["ok"] = False
        report["error"] = str(exc)

    if not report["credentials_found"]:
        report["notes"].append("Set GOOGLE_APPLICATION_CREDENTIALS to your OAuth or service-account JSON file.")
    if report["profile_loaded"] and not report["voice_available"]:
        report["notes"].append("Configured voice is not currently available in the selected language.")

    return report


def create_server(profile_file: str, profile_name: str) -> FastMCP:
    profile, client = load_runtime(profile_file, profile_name)

    mcp = FastMCP(
        name=f"GoogleTTS-{profile.name}",
        instructions=(
            "Text-to-speech server with fixed profile settings. "
            "Use tts_speak for generating and auto-playing local audio."
        ),
    )

    @mcp.tool
    def tts_speak(
        text: str = "",
        text_file: str = "",
        speaking_rate: float = profile.speaking_rate,
        pitch: float = profile.pitch,
    ) -> dict[str, Any]:
        """Generate speech with fixed voice/model/language/format and adjustable speaking rate and pitch."""
        try:
            resolved_text = read_text_input(text=text, text_file=text_file)
            output_file = timestamped_output_path(
                audio_format=profile.audio_format,
                output_dir=profile.output_dir,
                prefix=f"{profile.name}-tts",
            )

            result = synthesize_to_file(
                client,
                SynthesisRequest(
                    text=resolved_text,
                    ssml=False,
                    voice=profile.voice,
                    language=profile.language,
                    model=profile.model,
                    audio_format=profile.audio_format,
                    speaking_rate=speaking_rate,
                    pitch=pitch,
                    output_file=output_file,
                ),
            )

            now = datetime.now(UTC)
            append_usage_row(
                profile.usage_log,
                timestamp_utc=now,
                chars=result.chars,
                voice=result.voice,
                language=result.language,
                audio_format=result.audio_format,
                output_file=result.output_file,
            )
            usage = create_usage_snapshot(profile.usage_log, chars_this_request=result.chars, now_utc=now)

            played = False
            playback_error = ""
            try:
                played = play_audio(profile, result.output_file)
            except Exception as exc:  # noqa: BLE001
                playback_error = str(exc)

            response: dict[str, Any] = {
                "ok": True,
                "output_file": str(result.output_file),
                "mime_type": result.mime_type,
                "bytes": result.bytes_written,
                "chars": result.chars,
                "played": played,
                "profile": {
                    "name": profile.name,
                    "voice": profile.voice,
                    "language": profile.language,
                    "model": profile.model,
                    "format": profile.audio_format,
                    "speaking_rate": speaking_rate,
                    "pitch": pitch,
                },
                "usage": asdict(usage),
            }
            if playback_error:
                response["playback_error"] = playback_error
            return response
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "error": str(exc),
            }

    @mcp.tool
    def tts_doctor() -> dict[str, Any]:
        """Return auth/profile/playback diagnostics for the active TTS profile."""
        return doctor_report(profile_file, profile.name)

    @mcp.tool
    def tts_stop() -> dict[str, Any]:
        """Stop currently playing audio started by the configured player."""
        try:
            result = stop_audio(profile)
            return {
                "ok": True,
                "attempted": result.attempted,
                "player": result.player,
                "stopped_processes": result.stopped_processes,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "error": str(exc),
            }

    return mcp


def main() -> None:
    configure_logging(level="ERROR")
    args = parse_args()
    if args.doctor:
        print(json.dumps(doctor_report(args.profiles, args.profile), indent=2))
        return

    server = create_server(args.profiles, args.profile)
    server.run(show_banner=False)


if __name__ == "__main__":
    main()
