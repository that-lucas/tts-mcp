from __future__ import annotations

import sys

import pytest

from tts_mcp.list_voices import parse_args


def test_parse_args_defaults_no_family_filter(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["tts-voices"])
    args = parse_args()
    assert args.family == ""
    assert args.language == "en-US"
    assert args.limit == 0


def test_parse_args_explicit_family_still_supported(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["tts-voices", "--family", "Chirp3"])
    args = parse_args()
    assert args.family == "Chirp3"


def test_help_shows_defaults(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["tts-voices", "--help"])
    with pytest.raises(SystemExit):
        parse_args()
    out = capsys.readouterr().out
    assert "--language LANGUAGE" in out
    assert "default:" in out
    assert "en-US" in out
    assert "(default: )" in out
    assert "(default: 0)" in out
