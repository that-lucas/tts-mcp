from __future__ import annotations

from batch_generate_us import model_tag_and_name


def test_model_tag_chirp3():
    tag, model = model_tag_and_name("en-US-Chirp3-HD-Fenrir")
    assert tag == "chirp3"
    assert model == "models/chirp3-hd"


def test_model_tag_neural2():
    tag, model = model_tag_and_name("en-US-Neural2-D")
    assert tag == "neural2"
    assert model == ""


def test_model_tag_wavenet():
    tag, model = model_tag_and_name("en-US-WaveNet-C")
    assert tag == "wavenet"
    assert model == ""


def test_model_tag_unknown():
    tag, model = model_tag_and_name("en-US-Standard-A")
    assert tag == "generic"
    assert model == ""
