from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from google.cloud import texttospeech

AUDIO_ENCODINGS = {
    "mp3": texttospeech.AudioEncoding.MP3,
    "wav": texttospeech.AudioEncoding.LINEAR16,
    "ogg": texttospeech.AudioEncoding.OGG_OPUS,
}

MIME_TYPES = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "ogg": "audio/ogg",
}


@dataclass
class SynthesisRequest:
    text: str
    ssml: bool
    voice: str
    language: str
    model: str
    audio_format: str
    speaking_rate: float
    pitch: float
    output_file: Path


@dataclass
class SynthesisResult:
    output_file: Path
    mime_type: str
    bytes_written: int
    chars: int
    voice: str
    language: str
    model: str
    audio_format: str


def read_text_input(*, text: str, text_file: str) -> str:
    if text and text_file:
        raise ValueError("Use either text or text_file, not both.")
    if text:
        return text
    if text_file:
        source = Path(text_file).expanduser().resolve()
        if not source.exists():
            raise ValueError(f"Text file not found: {source}")
        return source.read_text(encoding="utf-8").strip()
    raise ValueError("No input text provided.")


def timestamped_output_path(*, audio_format: str, output_dir: Path, prefix: str = "speech") -> Path:
    now = datetime.now().astimezone()
    stamp = now.strftime("%Y%m%d-%H%M%S") + f"-{now.microsecond // 1000:03d}"
    if prefix.strip():
        safe_prefix = sanitize_filename(prefix)
        return output_dir / f"{safe_prefix}-{stamp}.{audio_format}"
    return output_dir / f"{stamp}.{audio_format}"


def sanitize_filename(value: str) -> str:
    keep = []
    for char in value:
        if char.isalnum() or char in {"-", "_", "."}:
            keep.append(char)
        else:
            keep.append("-")
    cleaned = "".join(keep).strip("-")
    return cleaned or "audio"


def synthesize_to_file(
    client: texttospeech.TextToSpeechClient,
    request: SynthesisRequest,
) -> SynthesisResult:
    if request.audio_format not in AUDIO_ENCODINGS:
        raise ValueError(f"Unsupported format: {request.audio_format}")

    if request.ssml:
        synthesis_input = texttospeech.SynthesisInput(ssml=request.text)
    else:
        synthesis_input = texttospeech.SynthesisInput(text=request.text)

    voice_name = request.voice.strip()
    language_code = request.language.strip()
    model_name = request.model.strip()
    if not voice_name and not language_code:
        raise ValueError("Either voice or language must be provided.")

    voice = texttospeech.VoiceSelectionParams()
    if language_code:
        voice.language_code = language_code
    if voice_name:
        voice.name = voice_name
    if model_name:
        voice.model_name = model_name

    response = client.synthesize_speech(
        request={
            "input": synthesis_input,
            "voice": voice,
            "audio_config": texttospeech.AudioConfig(
                audio_encoding=AUDIO_ENCODINGS[request.audio_format],
                speaking_rate=request.speaking_rate,
                pitch=request.pitch,
            ),
        }
    )

    request.output_file.parent.mkdir(parents=True, exist_ok=True)
    request.output_file.write_bytes(response.audio_content)

    return SynthesisResult(
        output_file=request.output_file,
        mime_type=MIME_TYPES[request.audio_format],
        bytes_written=len(response.audio_content),
        chars=len(request.text),
        voice=voice_name,
        language=language_code,
        model=model_name,
        audio_format=request.audio_format,
    )
