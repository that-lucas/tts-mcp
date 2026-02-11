from __future__ import annotations

from unittest.mock import MagicMock

from tts_core.voices import list_voices


def _make_voice(name, codes):
    v = MagicMock()
    v.name = name
    v.language_codes = codes
    return v


def _make_client(*voices):
    client = MagicMock()
    client.list_voices.return_value.voices = list(voices)
    return client


def test_list_voices_no_filter():
    client = _make_client(
        _make_voice("en-US-Chirp3-HD-A", ["en-US"]),
        _make_voice("en-US-Neural2-B", ["en-US"]),
    )
    result = list_voices(client)
    assert len(result) == 2
    assert result[0].name == "en-US-Chirp3-HD-A"


def test_list_voices_language_filter():
    client = _make_client(
        _make_voice("en-US-Chirp3-HD-A", ["en-US"]),
        _make_voice("fr-FR-Neural2-B", ["fr-FR"]),
    )
    result = list_voices(client, language="en-US")
    assert len(result) == 1
    assert result[0].name == "en-US-Chirp3-HD-A"


def test_list_voices_family_filter():
    client = _make_client(
        _make_voice("en-US-Chirp3-HD-A", ["en-US"]),
        _make_voice("en-US-Neural2-B", ["en-US"]),
    )
    result = list_voices(client, family="chirp3")
    assert len(result) == 1
    assert result[0].name == "en-US-Chirp3-HD-A"


def test_list_voices_limit():
    client = _make_client(
        _make_voice("a", ["en-US"]),
        _make_voice("b", ["en-US"]),
        _make_voice("c", ["en-US"]),
    )
    result = list_voices(client, limit=2)
    assert len(result) == 2


def test_list_voices_combined_filters():
    client = _make_client(
        _make_voice("en-US-Chirp3-HD-A", ["en-US"]),
        _make_voice("en-US-Neural2-B", ["en-US"]),
        _make_voice("fr-FR-Chirp3-HD-C", ["fr-FR"]),
    )
    result = list_voices(client, language="en-US", family="chirp3")
    assert len(result) == 1
    assert result[0].name == "en-US-Chirp3-HD-A"


def test_list_voices_empty():
    client = _make_client()
    result = list_voices(client)
    assert result == []
