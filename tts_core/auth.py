from __future__ import annotations

from google.auth.exceptions import DefaultCredentialsError
from google.cloud import texttospeech


def create_tts_client() -> texttospeech.TextToSpeechClient:
    try:
        return texttospeech.TextToSpeechClient()
    except DefaultCredentialsError as exc:
        raise RuntimeError(
            "Google credentials were not found. "
            "Run 'gcloud auth application-default login' or set GOOGLE_APPLICATION_CREDENTIALS."
        ) from exc
