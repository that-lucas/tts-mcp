from __future__ import annotations

import sys

from tts_mcp.list_voices import parse_args


def test_parse_args_defaults_no_family_filter(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["tts-voices"])
    args = parse_args()
    assert args.family == ""
    assert args.language == ""
    assert args.limit == 0


def test_parse_args_explicit_family_still_supported(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["tts-voices", "--family", "Chirp3"])
    args = parse_args()
    assert args.family == "Chirp3"
