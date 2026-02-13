from __future__ import annotations

import argparse
import sys

import pytest

from tts_mcp import batch
from tts_mcp.batch import model_tag_and_name
from tts_mcp.batch import parse_args as parse_batch_args


def test_model_tag_chirp3():
    tag, model = model_tag_and_name("en-US-Chirp3-HD-Fenrir")
    assert tag == "chirp3"
    assert model == "models/chirp3-hd"


def test_model_tag_neural2():
    tag, model = model_tag_and_name("en-US-Neural2-D")
    assert tag == "neural2"
    assert model == ""


def test_model_tag_wavenet():
    tag, model = model_tag_and_name("en-US-WaveNet-C")
    assert tag == "wavenet"
    assert model == ""


def test_model_tag_unknown():
    tag, model = model_tag_and_name("en-US-Standard-A")
    assert tag == "generic"
    assert model == ""


def test_parse_defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["tts-batch", "--text-file", "test.txt"])
    args = parse_batch_args()
    assert args.families == ""
    assert args.language == "en-US"
    assert args.format == "mp3"


def test_parse_explicit_filters(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["tts-batch", "--text-file", "test.txt", "--families", "Chirp3,Neural2", "--language", "fr-FR"],
    )
    args = parse_batch_args()
    assert args.families == "Chirp3,Neural2"
    assert args.language == "fr-FR"


def test_help_shows_defaults(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["tts-batch", "--help"])
    with pytest.raises(SystemExit):
        parse_batch_args()
    out = capsys.readouterr().out
    assert "(default: )" in out
    assert "--language LANGUAGE" in out
    assert "en-US" in out
    assert "--format {mp3,wav,ogg}" in out
    assert "default:" in out


def test_main_strips_language_and_family_filters(monkeypatch, tmp_path):
    args = argparse.Namespace(
        text_file=str(tmp_path / "text.txt"),
        out_dir=str(tmp_path / "out"),
        families=" Chirp3 , Neural2 ",
        language=" en-US ",
        format="mp3",
        speaking_rate=1.0,
        pitch=0.0,
        limit=0,
    )

    class VoiceRow:
        def __init__(self, name: str):
            self.name = name

    selected = [
        VoiceRow("en-US-Chirp3-HD-Fenrir"),
        VoiceRow("en-US-Neural2-D"),
        VoiceRow("en-US-Wavenet-C"),
    ]

    captured: dict[str, object] = {}
    requests = []
    dummy_client = object()

    monkeypatch.setattr(batch, "parse_args", lambda: args)
    monkeypatch.setattr(batch, "read_text_input", lambda **_: "hello")
    monkeypatch.setattr(batch, "create_tts_client", lambda: dummy_client)

    def _fake_list_voices(client, *, language, family, limit):
        captured["language"] = language
        captured["family"] = family
        captured["limit"] = limit
        return selected

    def _fake_synthesize_to_file(client, request):
        requests.append(request)

    monkeypatch.setattr(batch, "list_voices", _fake_list_voices)
    monkeypatch.setattr(batch, "synthesize_to_file", _fake_synthesize_to_file)

    batch.main()

    assert captured == {"language": "en-US", "family": "", "limit": 0}
    assert len(requests) == 2
    assert {request.voice for request in requests} == {"en-US-Chirp3-HD-Fenrir", "en-US-Neural2-D"}
    assert all(request.language == "en-US" for request in requests)
