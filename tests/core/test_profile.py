from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tts_mcp.core.profile import (
    TTSProfile,
    default_config_dir,
    load_profile,
    play_audio,
    resolve_profile_path,
    stop_audio,
)

# -- default_config_dir --


def test_default_config_dir_uses_xdg_env(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    assert default_config_dir() == (tmp_path / "xdg" / "tts-mcp")


def test_default_config_dir_uses_home_config_when_xdg_missing(monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    expected = Path("~/.config").expanduser() / "tts-mcp"
    assert default_config_dir() == expected


# -- resolve_profile_path --


def test_resolve_explicit_path(sample_profile_file):
    result = resolve_profile_path(str(sample_profile_file))
    assert result == sample_profile_file


def test_resolve_explicit_path_not_found(tmp_path):
    with pytest.raises(ValueError, match="not found"):
        resolve_profile_path(str(tmp_path / "nope.json"))


def test_resolve_xdg_path(tmp_path, monkeypatch):
    config_dir = tmp_path / ".config" / "tts-mcp"
    config_dir.mkdir(parents=True)
    profiles = config_dir / "profiles.json"
    profiles.write_text('{"profiles": {}}')
    monkeypatch.setattr("tts_mcp.core.profile.default_config_dir", lambda: config_dir)
    result = resolve_profile_path(None)
    assert result == profiles


def test_resolve_nothing_found(tmp_path, monkeypatch):
    monkeypatch.setattr("tts_mcp.core.profile.default_config_dir", lambda: tmp_path / "empty")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="tts-mcp --init"):
        resolve_profile_path(None)


def test_resolve_empty_string_treated_as_none(tmp_path, monkeypatch):
    """Empty string (from env var default) should trigger auto-discovery, not explicit lookup."""
    monkeypatch.setattr("tts_mcp.core.profile.default_config_dir", lambda: tmp_path / "empty")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="tts-mcp --init"):
        resolve_profile_path("")


# -- load_profile --


def test_load_profile_default(sample_profile_file):
    profile = load_profile(sample_profile_file, "")
    assert profile.name == "test"
    assert profile.voice == "en-US-Chirp3-HD-Fenrir"


def test_load_profile_named(sample_profile_file):
    profile = load_profile(sample_profile_file, "test")
    assert profile.name == "test"


def test_load_profile_missing_file(tmp_path):
    with pytest.raises(ValueError, match="not found"):
        load_profile(tmp_path / "nonexistent.json", "")


def test_load_profile_empty_profiles(tmp_path):
    f = tmp_path / "profiles.json"
    f.write_text(json.dumps({"profiles": {}}))
    with pytest.raises(ValueError, match="non-empty"):
        load_profile(f, "test")


def test_load_profile_unknown_name(sample_profile_file):
    with pytest.raises(ValueError, match="not found"):
        load_profile(sample_profile_file, "nonexistent")


def test_load_profile_no_default_no_name(tmp_path):
    data = {"profiles": {"a": {"voice": "v"}}}
    f = tmp_path / "profiles.json"
    f.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="No profile selected"):
        load_profile(f, "")


def test_load_profile_relative_paths(tmp_path):
    data = {
        "default_profile": "rp",
        "profiles": {
            "rp": {
                "voice": "v",
                "output_dir": "./myout",
                "usage_log": "./mylog.csv",
            }
        },
    }
    f = tmp_path / "profiles.json"
    f.write_text(json.dumps(data))
    profile = load_profile(f, "rp")
    assert profile.output_dir == (tmp_path / "myout").resolve()
    assert profile.usage_log == (tmp_path / "mylog.csv").resolve()


def test_load_profile_invalid_player_command(tmp_path):
    data = {
        "default_profile": "bad",
        "profiles": {"bad": {"voice": "v", "player_command": "not-a-list"}},
    }
    f = tmp_path / "profiles.json"
    f.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="list of strings"):
        load_profile(f, "bad")


# -- play_audio --


def _make_profile(**overrides) -> TTSProfile:
    defaults = {
        "name": "test",
        "voice": "v",
        "language": "en-US",
        "model": "",
        "audio_format": "mp3",
        "speaking_rate": 1.0,
        "pitch": 0.0,
        "output_dir": Path("/tmp/out"),
        "usage_log": Path("/tmp/usage.csv"),
        "autoplay": True,
        "player_command": ["afplay", "{file}"],
    }
    defaults.update(overrides)
    return TTSProfile(**defaults)


def test_play_audio_autoplay_off():
    profile = _make_profile(autoplay=False)
    assert play_audio(profile, Path("/tmp/test.mp3")) is False


@patch("tts_mcp.core.profile.subprocess.Popen")
@patch("tts_mcp.core.profile.shutil.which", return_value="/usr/bin/afplay")
def test_play_audio_success(mock_which, mock_popen):
    profile = _make_profile()
    result = play_audio(profile, Path("/tmp/test.mp3"))
    assert result is True
    mock_popen.assert_called_once()
    cmd = mock_popen.call_args.args[0]
    assert cmd == ["afplay", "/tmp/test.mp3"]


@patch("tts_mcp.core.profile.shutil.which", return_value=None)
def test_play_audio_player_not_found(mock_which):
    profile = _make_profile()
    with pytest.raises(RuntimeError, match="not found"):
        play_audio(profile, Path("/tmp/test.mp3"))


def test_play_audio_empty_command():
    profile = _make_profile(player_command=[])
    assert play_audio(profile, Path("/tmp/test.mp3")) is False


# -- stop_audio --


def test_stop_audio_no_player():
    profile = _make_profile(player_command=[])
    result = stop_audio(profile)
    assert result.attempted is False


def test_stop_audio_empty_player_name():
    profile = _make_profile(player_command=[""])
    result = stop_audio(profile)
    assert result.attempted is False
    assert result.player == ""


@patch("tts_mcp.core.profile.shutil.which")
@patch("tts_mcp.core.profile.subprocess.run")
def test_stop_audio_no_running(mock_run, mock_which):
    mock_which.side_effect = lambda x: f"/usr/bin/{x}"
    lookup = MagicMock()
    lookup.returncode = 1  # pgrep returns 1 when no processes found
    lookup.stdout = ""
    mock_run.return_value = lookup
    profile = _make_profile()
    result = stop_audio(profile)
    assert result.attempted is True
    assert result.stopped_processes == 0


@patch("tts_mcp.core.profile.shutil.which")
@patch("tts_mcp.core.profile.subprocess.run")
def test_stop_audio_kills_processes(mock_run, mock_which):
    mock_which.side_effect = lambda x: f"/usr/bin/{x}"

    lookup = MagicMock()
    lookup.returncode = 0
    lookup.stdout = "123\n456\n"

    kill = MagicMock()
    kill.returncode = 0

    mock_run.side_effect = [lookup, kill]
    profile = _make_profile()
    result = stop_audio(profile)
    assert result.attempted is True
    assert result.stopped_processes == 2


@patch("tts_mcp.core.profile.shutil.which", return_value=None)
def test_stop_audio_missing_tools(mock_which):
    profile = _make_profile()
    with pytest.raises(RuntimeError, match="missing"):
        stop_audio(profile)


@patch("tts_mcp.core.profile.shutil.which")
@patch("tts_mcp.core.profile.subprocess.run")
def test_stop_audio_lookup_failure(mock_run, mock_which):
    mock_which.side_effect = lambda x: f"/usr/bin/{x}"
    lookup = MagicMock()
    lookup.returncode = 2
    lookup.stdout = ""
    mock_run.return_value = lookup

    profile = _make_profile()
    with pytest.raises(RuntimeError, match="Failed to inspect"):
        stop_audio(profile)


@patch("tts_mcp.core.profile.shutil.which")
@patch("tts_mcp.core.profile.subprocess.run")
def test_stop_audio_falls_back_to_killall(mock_run, mock_which):
    def _which(name: str) -> str | None:
        if name == "pkill":
            return None
        return f"/usr/bin/{name}"

    mock_which.side_effect = _which
    lookup = MagicMock()
    lookup.returncode = 0
    lookup.stdout = "123\n"
    killall = MagicMock()
    killall.returncode = 0
    mock_run.side_effect = [lookup, killall]

    profile = _make_profile()
    result = stop_audio(profile)
    assert result.attempted is True
    assert result.stopped_processes == 1
    assert mock_run.call_args_list[1].args[0] == ["/usr/bin/killall", "afplay"]


@patch("tts_mcp.core.profile.shutil.which")
@patch("tts_mcp.core.profile.subprocess.run")
def test_stop_audio_stop_command_failure(mock_run, mock_which):
    mock_which.side_effect = lambda x: f"/usr/bin/{x}"
    lookup = MagicMock()
    lookup.returncode = 0
    lookup.stdout = "123\n"
    stop = MagicMock()
    stop.returncode = 1
    mock_run.side_effect = [lookup, stop]

    profile = _make_profile()
    with pytest.raises(RuntimeError, match="Failed to stop active playback"):
        stop_audio(profile)
