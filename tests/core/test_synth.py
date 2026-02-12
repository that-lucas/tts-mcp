from __future__ import annotations

import pytest

from tts_mcp.core.synth import (
    SynthesisRequest,
    read_text_input,
    sanitize_filename,
    synthesize_to_file,
    timestamped_output_path,
)

# -- read_text_input --


def test_read_text_input_direct_text():
    assert read_text_input(text="hello", text_file="") == "hello"


def test_read_text_input_from_file(tmp_path):
    f = tmp_path / "input.txt"
    f.write_text("from file")
    assert read_text_input(text="", text_file=str(f)) == "from file"


def test_read_text_input_both_raises():
    with pytest.raises(ValueError, match="not both"):
        read_text_input(text="a", text_file="b")


def test_read_text_input_neither_raises():
    with pytest.raises(ValueError, match="No input"):
        read_text_input(text="", text_file="")


def test_read_text_input_missing_file():
    with pytest.raises(ValueError, match="not found"):
        read_text_input(text="", text_file="/nonexistent/path.txt")


# -- timestamped_output_path --


def test_timestamped_output_path_format(tmp_path):
    result = timestamped_output_path(audio_format="wav", output_dir=tmp_path)
    assert result.suffix == ".wav"
    assert result.parent == tmp_path


def test_timestamped_output_path_mp3(tmp_path):
    result = timestamped_output_path(audio_format="mp3", output_dir=tmp_path)
    assert result.suffix == ".mp3"


# -- sanitize_filename --


def test_sanitize_filename_normal():
    assert sanitize_filename("hello-world") == "hello-world"


def test_sanitize_filename_special_chars():
    assert sanitize_filename("foo bar/baz") == "foo-bar-baz"


def test_sanitize_filename_empty():
    assert sanitize_filename("") == "audio"


def test_sanitize_filename_all_special():
    assert sanitize_filename("@#$") == "audio"


# -- synthesize_to_file --


def test_synthesize_to_file_mp3(mock_tts_client, tmp_path):
    output = tmp_path / "test.mp3"
    req = SynthesisRequest(
        text="hello",
        ssml=False,
        voice="en-US-Chirp3-HD-Fenrir",
        language="en-US",
        model="",
        audio_format="mp3",
        speaking_rate=1.0,
        pitch=0.0,
        output_file=output,
    )
    result = synthesize_to_file(mock_tts_client, req)

    assert result.output_file == output
    assert result.mime_type == "audio/mpeg"
    assert result.bytes_written == 128
    assert result.chars == 5
    assert result.voice == "en-US-Chirp3-HD-Fenrir"
    assert output.exists()


def test_synthesize_to_file_wav(mock_tts_client, tmp_path):
    output = tmp_path / "test.wav"
    req = SynthesisRequest(
        text="hi",
        ssml=False,
        voice="en-US-Neural2-D",
        language="en-US",
        model="",
        audio_format="wav",
        speaking_rate=1.0,
        pitch=0.0,
        output_file=output,
    )
    result = synthesize_to_file(mock_tts_client, req)
    assert result.mime_type == "audio/wav"
    assert output.exists()


def test_synthesize_to_file_ssml(mock_tts_client, tmp_path):
    output = tmp_path / "test.mp3"
    req = SynthesisRequest(
        text="<speak>Hello</speak>",
        ssml=True,
        voice="en-US-Chirp3-HD-Fenrir",
        language="en-US",
        model="",
        audio_format="mp3",
        speaking_rate=1.0,
        pitch=0.0,
        output_file=output,
    )
    synthesize_to_file(mock_tts_client, req)

    call_kwargs = mock_tts_client.synthesize_speech.call_args
    synthesis_input = call_kwargs.kwargs["request"]["input"]
    assert synthesis_input.ssml == "<speak>Hello</speak>"


def test_synthesize_to_file_with_model(mock_tts_client, tmp_path):
    output = tmp_path / "test.wav"
    req = SynthesisRequest(
        text="test",
        ssml=False,
        voice="en-US-Chirp3-HD-Fenrir",
        language="en-US",
        model="models/chirp3-hd",
        audio_format="wav",
        speaking_rate=1.0,
        pitch=0.0,
        output_file=output,
    )
    synthesize_to_file(mock_tts_client, req)

    call_kwargs = mock_tts_client.synthesize_speech.call_args
    voice_params = call_kwargs.kwargs["request"]["voice"]
    assert voice_params.model_name == "models/chirp3-hd"


def test_synthesize_to_file_without_model(mock_tts_client, tmp_path):
    output = tmp_path / "test.wav"
    req = SynthesisRequest(
        text="test",
        ssml=False,
        voice="en-US-Neural2-D",
        language="en-US",
        model="",
        audio_format="wav",
        speaking_rate=1.0,
        pitch=0.0,
        output_file=output,
    )
    synthesize_to_file(mock_tts_client, req)

    call_kwargs = mock_tts_client.synthesize_speech.call_args
    voice_params = call_kwargs.kwargs["request"]["voice"]
    assert not hasattr(voice_params, "model_name") or voice_params.model_name is None or voice_params.model_name == ""


def test_synthesize_to_file_bad_format(mock_tts_client, tmp_path):
    output = tmp_path / "test.aac"
    req = SynthesisRequest(
        text="test",
        ssml=False,
        voice="en-US-Chirp3-HD-Fenrir",
        language="en-US",
        model="",
        audio_format="aac",
        speaking_rate=1.0,
        pitch=0.0,
        output_file=output,
    )
    with pytest.raises(ValueError, match="Unsupported format"):
        synthesize_to_file(mock_tts_client, req)


def test_synthesize_creates_parent_dirs(mock_tts_client, tmp_path):
    output = tmp_path / "deep" / "nested" / "test.mp3"
    req = SynthesisRequest(
        text="test",
        ssml=False,
        voice="en-US-Chirp3-HD-Fenrir",
        language="en-US",
        model="",
        audio_format="mp3",
        speaking_rate=1.0,
        pitch=0.0,
        output_file=output,
    )
    result = synthesize_to_file(mock_tts_client, req)
    assert result.output_file.exists()
