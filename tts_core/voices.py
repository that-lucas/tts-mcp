from __future__ import annotations

from dataclasses import dataclass

from google.cloud import texttospeech


@dataclass
class VoiceEntry:
    name: str
    language_codes: list[str]


def list_voices(
    client: texttospeech.TextToSpeechClient,
    *,
    language: str = "",
    family: str = "",
    limit: int = 0,
) -> list[VoiceEntry]:
    language_filter = language.strip()
    family_filter = family.strip().lower()

    rows: list[VoiceEntry] = []
    for voice in client.list_voices().voices:
        if family_filter and family_filter not in voice.name.lower():
            continue
        if language_filter and language_filter not in voice.language_codes:
            continue
        rows.append(VoiceEntry(name=voice.name, language_codes=list(voice.language_codes)))

    rows.sort(key=lambda item: item.name)
    if limit > 0:
        rows = rows[:limit]
    return rows
