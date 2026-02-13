from __future__ import annotations

import sys

import pytest

from tts_mcp.speak import parse_args


def test_parse_defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["tts-speak"])
    args = parse_args()
    assert args.voice == ""
    assert args.language == "en-US"
    assert args.format == "mp3"


def test_help_shows_defaults(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["tts-speak", "--help"])
    with pytest.raises(SystemExit):
        parse_args()
    out = capsys.readouterr().out
    assert "(default: )" in out
    assert "--language LANGUAGE" in out
    assert "en-US" in out
    assert "--format {mp3,ogg,wav}" in out
    assert "default:" in out
