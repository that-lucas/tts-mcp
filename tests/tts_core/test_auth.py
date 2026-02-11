from __future__ import annotations

from unittest.mock import patch

import pytest

from tts_core.auth import create_tts_client


@patch("tts_core.auth.texttospeech.TextToSpeechClient")
def test_create_client_success(mock_cls):
    client = create_tts_client()
    mock_cls.assert_called_once()
    assert client is mock_cls.return_value


@patch("tts_core.auth.texttospeech.TextToSpeechClient")
def test_create_client_raises_on_missing_credentials(mock_cls):
    from google.auth.exceptions import DefaultCredentialsError

    mock_cls.side_effect = DefaultCredentialsError("no creds")
    with pytest.raises(RuntimeError, match="Google credentials were not found"):
        create_tts_client()
