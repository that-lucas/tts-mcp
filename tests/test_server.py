from __future__ import annotations

import argparse
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tts_mcp.server import create_server, doctor_report, init_config, load_runtime, main

# -- init_config --


def test_init_config_creates_file(tmp_path, monkeypatch):
    monkeypatch.setattr("tts_mcp.server.default_config_dir", lambda: tmp_path / "tts-mcp")
    dest = init_config()
    assert dest.exists()
    assert "profiles" in dest.read_text()


def test_init_config_refuses_overwrite(tmp_path, monkeypatch):
    config_dir = tmp_path / "tts-mcp"
    config_dir.mkdir()
    (config_dir / "profiles.json").write_text("{}")
    monkeypatch.setattr("tts_mcp.server.default_config_dir", lambda: config_dir)
    with pytest.raises(FileExistsError, match="already exists"):
        init_config(force=False)


def test_init_config_force_overwrites(tmp_path, monkeypatch):
    config_dir = tmp_path / "tts-mcp"
    config_dir.mkdir()
    (config_dir / "profiles.json").write_text("{}")
    monkeypatch.setattr("tts_mcp.server.default_config_dir", lambda: config_dir)
    dest = init_config(force=True)
    assert dest.exists()
    assert "profiles" in dest.read_text()


# -- doctor_report --


@patch("tts_mcp.server.load_runtime")
@patch("tts_mcp.server.list_voices")
def test_doctor_report_success(mock_voices, mock_lr, sample_profile_file):
    from tts_mcp.core.profile import load_profile

    profile = load_profile(sample_profile_file, "test")
    client = MagicMock()
    mock_lr.return_value = (profile, client)

    voice = MagicMock()
    voice.name = profile.voice
    mock_voices.return_value = [voice]

    report = doctor_report(str(sample_profile_file), "test")
    assert report["ok"] is True
    assert report["profile_loaded"] is True
    assert report["client_ready"] is True
    assert report["voice_available"] is True


@patch("tts_mcp.server.load_runtime")
@patch("tts_mcp.server.list_voices")
def test_doctor_report_env_credentials_source(mock_voices, mock_lr, sample_profile_file, monkeypatch):
    from tts_mcp.core.profile import load_profile

    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/adc.json")

    profile = load_profile(sample_profile_file, "test")
    mock_lr.return_value = (profile, MagicMock())
    voice = MagicMock()
    voice.name = profile.voice
    mock_voices.return_value = [voice]

    report = doctor_report(str(sample_profile_file), "test")
    assert report["credentials_source"] == "env_var"
    assert report["credentials_path"] == "/tmp/adc.json"


@patch("tts_mcp.server.load_runtime", side_effect=RuntimeError("bad runtime"))
@patch("tts_mcp.server.resolve_profile_path", side_effect=ValueError("missing"))
def test_doctor_report_uses_input_path_when_resolution_fails(mock_resolve, mock_lr):
    report = doctor_report("/tmp/missing.json", "")
    assert report["profile_file"] == "/tmp/missing.json"
    assert report["ok"] is False


@patch("tts_mcp.server.shutil.which", return_value=None)
@patch("tts_mcp.server.load_runtime")
@patch("tts_mcp.server.list_voices")
def test_doctor_report_player_missing_note(mock_voices, mock_lr, mock_which, sample_profile_file):
    from tts_mcp.core.profile import load_profile

    profile = load_profile(sample_profile_file, "test")
    profile.autoplay = True
    profile.player_command = ["missing-player", "{file}"]
    mock_lr.return_value = (profile, MagicMock())

    voice = MagicMock()
    voice.name = profile.voice
    mock_voices.return_value = [voice]

    report = doctor_report(str(sample_profile_file), "test")
    assert report["player_available"] is False
    assert any("Audio player not found" in note for note in report["notes"])


@patch("tts_mcp.server.load_runtime", side_effect=RuntimeError("boom"))
def test_doctor_report_load_failure(mock_lr, sample_profile_file):
    report = doctor_report(str(sample_profile_file), "test")
    assert report["ok"] is False
    assert "boom" in report["error"]


@patch("tts_mcp.server.load_runtime")
@patch("tts_mcp.server.list_voices")
def test_doctor_report_no_credentials(mock_voices, mock_lr, sample_profile_file, monkeypatch, tmp_path):
    from tts_mcp.core.profile import load_profile

    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    # Point HOME to an empty temp dir so the gcloud ADC well-known path doesn't exist
    monkeypatch.setenv("HOME", str(tmp_path))

    profile = load_profile(sample_profile_file, "test")
    mock_lr.return_value = (profile, MagicMock())
    mock_voices.return_value = []

    report = doctor_report(str(sample_profile_file), "test")
    assert report["credentials_source"] == "not_found"
    assert any("gcloud" in n for n in report["notes"])


@patch("tts_mcp.server.load_runtime")
@patch("tts_mcp.server.list_voices")
def test_doctor_report_voice_not_available(mock_voices, mock_lr, sample_profile_file):
    from tts_mcp.core.profile import load_profile

    profile = load_profile(sample_profile_file, "test")
    mock_lr.return_value = (profile, MagicMock())

    other_voice = MagicMock()
    other_voice.name = "en-US-Neural2-D"
    mock_voices.return_value = [other_voice]

    report = doctor_report(str(sample_profile_file), "test")
    assert report["voice_available"] is False
    assert any("not currently available" in n for n in report["notes"])


# -- create_server --


@patch("tts_mcp.server.load_runtime")
def test_create_server_returns_fastmcp(mock_lr, sample_profile_file):
    from fastmcp import FastMCP

    from tts_mcp.core.profile import load_profile

    profile = load_profile(sample_profile_file, "test")
    mock_lr.return_value = (profile, MagicMock())
    server = create_server(str(sample_profile_file), "test")
    assert isinstance(server, FastMCP)
    assert profile.name in server.name


@patch("tts_mcp.server.create_tts_client")
@patch("tts_mcp.server.load_profile")
@patch("tts_mcp.server.resolve_profile_path")
def test_load_runtime_resolves_profile_and_client(mock_resolve, mock_load_profile, mock_create_client):
    resolved = MagicMock()
    profile = MagicMock()
    client = MagicMock()

    mock_resolve.return_value = resolved
    mock_load_profile.return_value = profile
    mock_create_client.return_value = client

    got_profile, got_client = load_runtime("/tmp/profiles.json", "demo")
    assert got_profile is profile
    assert got_client is client
    mock_resolve.assert_called_once_with("/tmp/profiles.json")
    mock_load_profile.assert_called_once_with(resolved, "demo")
    mock_create_client.assert_called_once()


# -- tool functions (via closure extraction) --


@patch("tts_mcp.server.load_runtime")
@patch("tts_mcp.server.synthesize_to_file")
@patch("tts_mcp.server.play_audio", return_value=False)
def test_tts_speak_tool_success(mock_play, mock_synth, mock_lr, sample_profile_file, tmp_path):
    from tts_mcp.core.profile import load_profile
    from tts_mcp.core.synth import SynthesisResult

    profile = load_profile(sample_profile_file, "test")
    mock_lr.return_value = (profile, MagicMock())

    output = tmp_path / "out" / "test.mp3"
    output.parent.mkdir(parents=True, exist_ok=True)
    mock_synth.return_value = SynthesisResult(
        output_file=output,
        mime_type="audio/mpeg",
        bytes_written=128,
        chars=5,
        voice=profile.voice,
        language=profile.language,
        model=profile.model,
        audio_format=profile.audio_format,
    )

    server = create_server(str(sample_profile_file), "test")
    speak_tool: Any = server._tool_manager._tools["tts_speak"]
    result = speak_tool.fn(text="hello")
    assert result["ok"] is True
    assert result["chars"] == 5


@patch("tts_mcp.server.load_runtime")
@patch("tts_mcp.server.synthesize_to_file")
@patch("tts_mcp.server.play_audio", side_effect=RuntimeError("player failed"))
def test_tts_speak_tool_reports_playback_error(mock_play, mock_synth, mock_lr, sample_profile_file, tmp_path):
    from tts_mcp.core.profile import load_profile
    from tts_mcp.core.synth import SynthesisResult

    profile = load_profile(sample_profile_file, "test")
    mock_lr.return_value = (profile, MagicMock())

    output = tmp_path / "out" / "test.mp3"
    output.parent.mkdir(parents=True, exist_ok=True)
    mock_synth.return_value = SynthesisResult(
        output_file=output,
        mime_type="audio/mpeg",
        bytes_written=128,
        chars=5,
        voice=profile.voice,
        language=profile.language,
        model=profile.model,
        audio_format=profile.audio_format,
    )

    server = create_server(str(sample_profile_file), "test")
    speak_tool: Any = server._tool_manager._tools["tts_speak"]
    result = speak_tool.fn(text="hello")
    assert result["ok"] is True
    assert result["playback_error"] == "player failed"


@patch("tts_mcp.server.load_runtime")
@patch("tts_mcp.server.read_text_input", side_effect=ValueError("bad input"))
def test_tts_speak_tool_error(mock_read, mock_lr, sample_profile_file):
    from tts_mcp.core.profile import load_profile

    profile = load_profile(sample_profile_file, "test")
    mock_lr.return_value = (profile, MagicMock())

    server = create_server(str(sample_profile_file), "test")
    speak_tool: Any = server._tool_manager._tools["tts_speak"]
    result = speak_tool.fn(text="hello")
    assert result["ok"] is False
    assert "bad input" in result["error"]


@patch("tts_mcp.server.load_runtime")
@patch("tts_mcp.server.stop_audio")
def test_tts_stop_tool(mock_stop, mock_lr, sample_profile_file):
    from tts_mcp.core.profile import StopAudioResult, load_profile

    profile = load_profile(sample_profile_file, "test")
    mock_lr.return_value = (profile, MagicMock())
    mock_stop.return_value = StopAudioResult(attempted=True, player="afplay", stopped_processes=1)

    server = create_server(str(sample_profile_file), "test")
    stop_tool: Any = server._tool_manager._tools["tts_stop"]
    result = stop_tool.fn()
    assert result["ok"] is True
    assert result["stopped_processes"] == 1


@patch("tts_mcp.server.load_runtime")
@patch("tts_mcp.server.stop_audio", side_effect=RuntimeError("cannot stop"))
def test_tts_stop_tool_error(mock_stop, mock_lr, sample_profile_file):
    from tts_mcp.core.profile import load_profile

    profile = load_profile(sample_profile_file, "test")
    mock_lr.return_value = (profile, MagicMock())

    server = create_server(str(sample_profile_file), "test")
    stop_tool: Any = server._tool_manager._tools["tts_stop"]
    result = stop_tool.fn()
    assert result["ok"] is False
    assert "cannot stop" in result["error"]


@patch("tts_mcp.server.load_runtime")
@patch("tts_mcp.server.doctor_report", return_value={"ok": True, "note": "hi"})
def test_tts_doctor_tool_calls_doctor_report(mock_doctor, mock_lr, sample_profile_file):
    from tts_mcp.core.profile import load_profile

    profile = load_profile(sample_profile_file, "test")
    mock_lr.return_value = (profile, MagicMock())

    server = create_server(str(sample_profile_file), "test")
    doctor_tool: Any = server._tool_manager._tools["tts_doctor"]
    result = doctor_tool.fn()
    assert result == {"ok": True, "note": "hi"}
    mock_doctor.assert_called_once_with(str(sample_profile_file), profile.name)


# -- main --


@patch("tts_mcp.server.init_config")
@patch("tts_mcp.server.parse_args")
@patch("tts_mcp.server.configure_logging")
def test_main_init_branch_success(mock_logging, mock_parse, mock_init, capsys):
    mock_parse.return_value = argparse.Namespace(init=True, force=False, doctor=False, profiles="", profile="")
    mock_init.return_value = "/tmp/profiles.json"

    main()
    out = capsys.readouterr().out
    assert "Created /tmp/profiles.json" in out


@patch("tts_mcp.server.init_config", side_effect=FileExistsError("already exists"))
@patch("tts_mcp.server.parse_args")
@patch("tts_mcp.server.configure_logging")
def test_main_init_branch_failure_exits(mock_logging, mock_parse, mock_init, capsys):
    mock_parse.return_value = argparse.Namespace(init=True, force=False, doctor=False, profiles="", profile="")

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    assert "already exists" in capsys.readouterr().out


@patch("tts_mcp.server.doctor_report", return_value={"ok": True})
@patch("tts_mcp.server.parse_args")
@patch("tts_mcp.server.configure_logging")
def test_main_doctor_branch(mock_logging, mock_parse, mock_doctor, capsys):
    mock_parse.return_value = argparse.Namespace(
        init=False, force=False, doctor=True, profiles="/tmp/p.json", profile="demo"
    )

    main()
    out = capsys.readouterr().out
    assert '"ok": true' in out
    mock_doctor.assert_called_once_with("/tmp/p.json", "demo")


@patch("tts_mcp.server.create_server")
@patch("tts_mcp.server.parse_args")
@patch("tts_mcp.server.configure_logging")
def test_main_runs_server(mock_logging, mock_parse, mock_create_server):
    mock_parse.return_value = argparse.Namespace(
        init=False, force=False, doctor=False, profiles="/tmp/p.json", profile="demo"
    )
    server = MagicMock()
    mock_create_server.return_value = server

    main()
    mock_create_server.assert_called_once_with("/tmp/p.json", "demo")
    server.run.assert_called_once_with(show_banner=False)
