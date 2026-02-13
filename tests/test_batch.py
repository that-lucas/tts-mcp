from __future__ import annotations

import sys

import pytest

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
