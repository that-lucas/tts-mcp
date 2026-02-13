from __future__ import annotations

import sys

import pytest

from tts_mcp.server import PROFILE_NAME_ENV, PROFILES_ENV, parse_args


def test_parse_defaults_no_env(monkeypatch):
    monkeypatch.delenv(PROFILES_ENV, raising=False)
    monkeypatch.delenv(PROFILE_NAME_ENV, raising=False)
    monkeypatch.setattr(sys, "argv", ["tts-mcp"])
    args = parse_args()
    assert args.profiles == ""
    assert args.profile == ""
    assert args.doctor is False
    assert args.init is False
    assert args.force is False


def test_parse_uses_new_env_vars(monkeypatch):
    monkeypatch.setenv(PROFILES_ENV, "/tmp/profiles.json")
    monkeypatch.setenv(PROFILE_NAME_ENV, "demo")
    monkeypatch.setattr(sys, "argv", ["tts-mcp"])
    args = parse_args()
    assert args.profiles == "/tmp/profiles.json"
    assert args.profile == "demo"


def test_parse_ignores_legacy_env_vars(monkeypatch):
    monkeypatch.delenv(PROFILES_ENV, raising=False)
    monkeypatch.delenv(PROFILE_NAME_ENV, raising=False)
    monkeypatch.setenv("GTTS_PROFILES", "/tmp/legacy.json")
    monkeypatch.setenv("GTTS_PROFILE", "legacy")
    monkeypatch.setattr(sys, "argv", ["tts-mcp"])
    args = parse_args()
    assert args.profiles == ""
    assert args.profile == ""


def test_help_shows_defaults(monkeypatch, capsys):
    monkeypatch.delenv(PROFILES_ENV, raising=False)
    monkeypatch.delenv(PROFILE_NAME_ENV, raising=False)
    monkeypatch.setattr(sys, "argv", ["tts-mcp", "--help"])
    with pytest.raises(SystemExit):
        parse_args()
    out = capsys.readouterr().out
    assert "(default: )" in out
    assert "--doctor" in out
    assert "--init" in out
    assert "--force" in out
