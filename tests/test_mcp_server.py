from __future__ import annotations

from unittest.mock import MagicMock, patch

from mcp_server import create_server, doctor_report

# -- doctor_report --


@patch("mcp_server.load_runtime")
@patch("mcp_server.list_voices")
def test_doctor_report_success(mock_voices, mock_lr, sample_profile_file):
    from tts_core.profile import load_profile

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


@patch("mcp_server.load_runtime", side_effect=RuntimeError("boom"))
def test_doctor_report_load_failure(mock_lr, sample_profile_file):
    report = doctor_report(str(sample_profile_file), "test")
    assert report["ok"] is False
    assert "boom" in report["error"]


@patch("mcp_server.load_runtime")
@patch("mcp_server.list_voices")
def test_doctor_report_no_credentials(mock_voices, mock_lr, sample_profile_file, monkeypatch, tmp_path):
    from tts_core.profile import load_profile

    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    # Point HOME to an empty temp dir so the gcloud ADC well-known path doesn't exist
    monkeypatch.setenv("HOME", str(tmp_path))

    profile = load_profile(sample_profile_file, "test")
    mock_lr.return_value = (profile, MagicMock())
    mock_voices.return_value = []

    report = doctor_report(str(sample_profile_file), "test")
    assert report["credentials_source"] == "not_found"
    assert any("gcloud" in n for n in report["notes"])


@patch("mcp_server.load_runtime")
@patch("mcp_server.list_voices")
def test_doctor_report_voice_not_available(mock_voices, mock_lr, sample_profile_file):
    from tts_core.profile import load_profile

    profile = load_profile(sample_profile_file, "test")
    mock_lr.return_value = (profile, MagicMock())

    other_voice = MagicMock()
    other_voice.name = "en-US-Neural2-D"
    mock_voices.return_value = [other_voice]

    report = doctor_report(str(sample_profile_file), "test")
    assert report["voice_available"] is False
    assert any("not currently available" in n for n in report["notes"])


# -- create_server --


@patch("mcp_server.load_runtime")
def test_create_server_returns_fastmcp(mock_lr, sample_profile_file):
    from fastmcp import FastMCP

    from tts_core.profile import load_profile

    profile = load_profile(sample_profile_file, "test")
    mock_lr.return_value = (profile, MagicMock())
    server = create_server(str(sample_profile_file), "test")
    assert isinstance(server, FastMCP)
    assert profile.name in server.name


# -- tool functions (via closure extraction) --


@patch("mcp_server.load_runtime")
@patch("mcp_server.synthesize_to_file")
@patch("mcp_server.play_audio", return_value=False)
def test_tts_speak_tool_success(mock_play, mock_synth, mock_lr, sample_profile_file, tmp_path):
    from tts_core.profile import load_profile
    from tts_core.synth import SynthesisResult

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
    speak_tool = server._tool_manager._tools["tts_speak"]
    result = speak_tool.fn(text="hello")
    assert result["ok"] is True
    assert result["chars"] == 5


@patch("mcp_server.load_runtime")
@patch("mcp_server.read_text_input", side_effect=ValueError("bad input"))
def test_tts_speak_tool_error(mock_read, mock_lr, sample_profile_file):
    from tts_core.profile import load_profile

    profile = load_profile(sample_profile_file, "test")
    mock_lr.return_value = (profile, MagicMock())

    server = create_server(str(sample_profile_file), "test")
    speak_tool = server._tool_manager._tools["tts_speak"]
    result = speak_tool.fn(text="hello")
    assert result["ok"] is False
    assert "bad input" in result["error"]


@patch("mcp_server.load_runtime")
@patch("mcp_server.stop_audio")
def test_tts_stop_tool(mock_stop, mock_lr, sample_profile_file):
    from tts_core.profile import StopAudioResult, load_profile

    profile = load_profile(sample_profile_file, "test")
    mock_lr.return_value = (profile, MagicMock())
    mock_stop.return_value = StopAudioResult(attempted=True, player="afplay", stopped_processes=1)

    server = create_server(str(sample_profile_file), "test")
    stop_tool = server._tool_manager._tools["tts_stop"]
    result = stop_tool.fn()
    assert result["ok"] is True
    assert result["stopped_processes"] == 1
