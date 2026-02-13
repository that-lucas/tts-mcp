from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_tts_client():
    """A MagicMock standing in for texttospeech.TextToSpeechClient."""
    client = MagicMock()
    response = MagicMock()
    response.audio_content = b"\x00" * 128
    client.synthesize_speech.return_value = response
    return client


@pytest.fixture
def sample_profile_dict(tmp_path):
    """Return a minimal profile dict and the path to its JSON file."""
    data = {
        "default_profile": "test",
        "profiles": {
            "test": {
                "voice": "en-US-Chirp3-HD-Fenrir",
                "language": "en-US",
                "model": "",
                "format": "mp3",
                "speaking_rate": 1.0,
                "pitch": 0.0,
                "output_dir": str(tmp_path / "out"),
                "usage_log": str(tmp_path / "usage.csv"),
                "autoplay": False,
                "player_command": ["afplay", "{file}"],
            }
        },
    }
    return data


@pytest.fixture
def sample_profile_file(tmp_path, sample_profile_dict):
    """Write a minimal profiles.json and return its Path."""
    f = tmp_path / "profiles.json"
    f.write_text(json.dumps(sample_profile_dict))
    return f
