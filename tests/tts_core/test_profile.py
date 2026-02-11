from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tts_core.profile import TTSProfile, load_profile, play_audio, stop_audio

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


@patch("tts_core.profile.subprocess.Popen")
@patch("tts_core.profile.shutil.which", return_value="/usr/bin/afplay")
def test_play_audio_success(mock_which, mock_popen):
    profile = _make_profile()
    result = play_audio(profile, Path("/tmp/test.mp3"))
    assert result is True
    mock_popen.assert_called_once()
    cmd = mock_popen.call_args.args[0]
    assert cmd == ["afplay", "/tmp/test.mp3"]


@patch("tts_core.profile.shutil.which", return_value=None)
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


@patch("tts_core.profile.shutil.which")
@patch("tts_core.profile.subprocess.run")
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


@patch("tts_core.profile.shutil.which")
@patch("tts_core.profile.subprocess.run")
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


@patch("tts_core.profile.shutil.which", return_value=None)
def test_stop_audio_missing_tools(mock_which):
    profile = _make_profile()
    with pytest.raises(RuntimeError, match="missing"):
        stop_audio(profile)
