from __future__ import annotations

import io
import re
import sys

import pytest

from tts_mcp import speak
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
    assert "reads piped stdin" in out
    assert "prompts interactively" in out


def test_read_text_fallback_uses_piped_stdin(monkeypatch):
    monkeypatch.setattr(speak.sys, "stdin", io.StringIO("hello from pipe\n"))
    assert speak._read_text_fallback() == "hello from pipe\n"


def test_read_text_fallback_prompts_when_tty(monkeypatch):
    class DummyStdin:
        @staticmethod
        def isatty() -> bool:
            return True

        @staticmethod
        def read() -> str:
            return ""

    monkeypatch.setattr(speak.sys, "stdin", DummyStdin())
    monkeypatch.setattr("builtins.input", lambda _: "  typed text  ")
    assert speak._read_text_fallback() == "typed text"


def test_resolve_output_path_uses_local_timestamp_format(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["tts-speak"])
    args = parse_args()
    output = speak._resolve_output_path(args)
    assert output.is_absolute()
    assert re.match(r"^\d{8}-\d{6}-\d{3}\.mp3$", output.name)
