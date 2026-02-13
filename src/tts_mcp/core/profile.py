from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

CONFIG_DIR_NAME = "tts-mcp"
PROFILES_FILENAME = "profiles.json"


@dataclass
class TTSProfile:
    name: str
    voice: str
    language: str
    model: str
    audio_format: str
    speaking_rate: float
    pitch: float
    output_dir: Path
    usage_log: Path
    autoplay: bool
    player_command: list[str]


@dataclass
class StopAudioResult:
    attempted: bool
    player: str
    stopped_processes: int


def default_config_dir() -> Path:
    """Return the XDG config directory for tts-mcp.

    Honors XDG_CONFIG_HOME if set, otherwise defaults to ~/.config.
    """
    xdg_config = os.environ.get("XDG_CONFIG_HOME", "")
    base = Path(xdg_config).expanduser() if xdg_config else Path("~/.config").expanduser()
    return base / CONFIG_DIR_NAME


def resolve_profile_path(explicit: str | None = None) -> Path:
    """Find the profiles file, searching in priority order.

    1. Explicit path (--profiles flag or TTS_MCP_PROFILES_PATH env var)
    2. ~/.config/tts-mcp/profiles.json  (XDG standard)

    Raises ValueError with a helpful message if nothing is found.
    """
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if path.exists():
            return path
        raise ValueError(f"Profile file not found: {path}")

    xdg_path = default_config_dir() / PROFILES_FILENAME
    if xdg_path.exists():
        return xdg_path

    raise ValueError(
        "No profiles file found.\n"
        "Run 'tts-mcp --init' to create one at ~/.config/tts-mcp/profiles.json\n"
        "or specify a path with --profiles or the TTS_MCP_PROFILES_PATH env var."
    )


def _resolve_path(base_dir: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return path


def load_profile(profile_file: Path, profile_name: str) -> TTSProfile:
    source = profile_file.expanduser().resolve()
    if not source.exists():
        raise ValueError(f"Profile file not found: {source}")

    raw = json.loads(source.read_text(encoding="utf-8"))
    profiles = raw.get("profiles", {})
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("Profile file must contain a non-empty 'profiles' object.")

    selected_name = profile_name or raw.get("default_profile", "")
    if not selected_name:
        raise ValueError("No profile selected and no default_profile defined.")

    selected = profiles.get(selected_name)
    if not isinstance(selected, dict):
        raise ValueError(f"Profile not found: {selected_name}")

    base_dir = source.parent
    output_dir = _resolve_path(base_dir, selected.get("output_dir", "./out"))
    usage_log = _resolve_path(base_dir, selected.get("usage_log", "usage_log.csv"))

    player = selected.get("player_command", ["afplay", "{file}"])
    if not isinstance(player, list) or not all(isinstance(item, str) for item in player):
        raise ValueError("profile.player_command must be a list of strings")

    return TTSProfile(
        name=selected_name,
        voice=str(selected.get("voice", "en-US-Chirp3-HD-Fenrir")),
        language=str(selected.get("language", "en-US")),
        model=str(selected.get("model", "")),
        audio_format=str(selected.get("format", "mp3")),
        speaking_rate=float(selected.get("speaking_rate", 1.0)),
        pitch=float(selected.get("pitch", 0.0)),
        output_dir=output_dir,
        usage_log=usage_log,
        autoplay=bool(selected.get("autoplay", True)),
        player_command=player,
    )


def play_audio(profile: TTSProfile, file_path: Path) -> bool:
    if not profile.autoplay:
        return False

    command = [part.replace("{file}", str(file_path)) for part in profile.player_command]
    if not command:
        return False

    if shutil.which(command[0]) is None:
        raise RuntimeError(f"Audio player not found: {command[0]}")

    subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return True


def stop_audio(profile: TTSProfile) -> StopAudioResult:
    if not profile.player_command:
        return StopAudioResult(attempted=False, player="", stopped_processes=0)

    player = Path(profile.player_command[0]).name
    if not player:
        return StopAudioResult(attempted=False, player="", stopped_processes=0)

    pgrep_cmd = shutil.which("pgrep")
    pkill_cmd = shutil.which("pkill")
    killall_cmd = shutil.which("killall")

    if pgrep_cmd is None or (pkill_cmd is None and killall_cmd is None):
        raise RuntimeError("Unable to stop playback automatically: missing pgrep/pkill tools")

    lookup = subprocess.run([pgrep_cmd, "-x", player], capture_output=True, text=True, check=False)
    if lookup.returncode not in (0, 1):
        raise RuntimeError(f"Failed to inspect running player processes for: {player}")

    running = [line.strip() for line in lookup.stdout.splitlines() if line.strip()]
    running_count = len(running)
    if running_count == 0:
        return StopAudioResult(attempted=True, player=player, stopped_processes=0)

    if pkill_cmd is not None:
        stop = subprocess.run([pkill_cmd, "-x", player], check=False)
    else:
        if killall_cmd is None:
            raise RuntimeError("Unable to stop playback automatically: missing killall")
        stop = subprocess.run([killall_cmd, player], check=False)

    if stop.returncode != 0:
        raise RuntimeError(f"Failed to stop active playback for player: {player}")

    return StopAudioResult(attempted=True, player=player, stopped_processes=running_count)
