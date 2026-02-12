from __future__ import annotations

import csv
from datetime import UTC, datetime

from tts_mcp.core.usage import (
    append_usage_row,
    create_usage_snapshot,
    detect_family,
    month_chars_by_family,
    month_total_chars,
)


def test_append_usage_row_creates_file(tmp_path):
    log = tmp_path / "usage.csv"
    now = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)
    append_usage_row(
        log,
        timestamp_utc=now,
        chars=42,
        voice="en-US-Neural2-D",
        language="en-US",
        audio_format="mp3",
        output_file=tmp_path / "test.mp3",
    )
    assert log.exists()
    with log.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["chars"] == "42"
    assert rows[0]["month"] == "2025-06"


def test_append_usage_row_appends(tmp_path):
    log = tmp_path / "usage.csv"
    now = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)
    for i in range(3):
        append_usage_row(
            log,
            timestamp_utc=now,
            chars=10 + i,
            voice="en-US-Neural2-D",
            language="en-US",
            audio_format="mp3",
            output_file=tmp_path / f"test{i}.mp3",
        )
    with log.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 3


def test_append_usage_row_creates_dirs(tmp_path):
    log = tmp_path / "sub" / "dir" / "usage.csv"
    now = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)
    append_usage_row(
        log,
        timestamp_utc=now,
        chars=5,
        voice="en-US-Neural2-D",
        language="en-US",
        audio_format="mp3",
        output_file=tmp_path / "test.mp3",
    )
    assert log.exists()


def test_month_total_chars_empty(tmp_path):
    assert month_total_chars(tmp_path / "nope.csv", "2025-06") == 0


def test_month_total_chars_sums_month(tmp_path):
    log = tmp_path / "usage.csv"
    june = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)
    july = datetime(2025, 7, 1, 12, 0, 0, tzinfo=UTC)
    for ts, chars in [(june, 10), (june, 20), (july, 100)]:
        append_usage_row(
            log,
            timestamp_utc=ts,
            chars=chars,
            voice="en-US-Neural2-D",
            language="en-US",
            audio_format="mp3",
            output_file=tmp_path / "test.mp3",
        )
    assert month_total_chars(log, "2025-06") == 30
    assert month_total_chars(log, "2025-07") == 100


def test_month_total_chars_wrong_month(tmp_path):
    log = tmp_path / "usage.csv"
    now = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)
    append_usage_row(
        log,
        timestamp_utc=now,
        chars=10,
        voice="en-US-Neural2-D",
        language="en-US",
        audio_format="mp3",
        output_file=tmp_path / "test.mp3",
    )
    assert month_total_chars(log, "2025-01") == 0


# -- detect_family --


def test_detect_family_chirp3():
    assert detect_family("en-US-Chirp3-HD-Fenrir") == "Chirp3-HD"


def test_detect_family_neural2():
    assert detect_family("en-US-Neural2-D") == "Neural2"


def test_detect_family_wavenet():
    assert detect_family("en-US-Wavenet-D") == "Wavenet"


def test_detect_family_unknown():
    assert detect_family("some-weird-voice") == "Unknown"


# -- month_chars_by_family --


def test_month_chars_by_family_empty(tmp_path):
    assert month_chars_by_family(tmp_path / "nope.csv", "2025-06") == {}


def test_month_chars_by_family_groups(tmp_path):
    log = tmp_path / "usage.csv"
    now = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)
    for voice, chars in [
        ("en-US-Chirp3-HD-Fenrir", 100),
        ("en-US-Chirp3-HD-Achird", 200),
        ("en-US-Neural2-D", 50),
        ("en-US-Wavenet-D", 75),
    ]:
        append_usage_row(
            log,
            timestamp_utc=now,
            chars=chars,
            voice=voice,
            language="en-US",
            audio_format="mp3",
            output_file=tmp_path / "test.mp3",
        )
    result = month_chars_by_family(log, "2025-06")
    assert result["Chirp3-HD"] == 300
    assert result["Neural2"] == 50
    assert result["Wavenet"] == 75


# -- create_usage_snapshot --


def test_create_usage_snapshot_single_family(tmp_path):
    log = tmp_path / "usage.csv"
    now = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)
    append_usage_row(
        log,
        timestamp_utc=now,
        chars=50,
        voice="en-US-Neural2-D",
        language="en-US",
        audio_format="mp3",
        output_file=tmp_path / "test.mp3",
    )
    snapshot = create_usage_snapshot(log, chars_this_request=50, voice="en-US-Neural2-D", now_utc=now)
    assert snapshot.chars_this_request == 50
    assert snapshot.voice_family == "Neural2"
    assert snapshot.month_key == "2025-06"
    assert "Neural2" in snapshot.month_to_date_by_family
    fu = snapshot.month_to_date_by_family["Neural2"]
    assert fu.chars == 50
    assert fu.free_tier == 1_000_000
    assert fu.billable_chars == 0
    assert fu.estimated_cost_usd == 0.0


def test_create_usage_snapshot_multiple_families(tmp_path):
    log = tmp_path / "usage.csv"
    now = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)
    for voice, chars in [
        ("en-US-Chirp3-HD-Fenrir", 500_000),
        ("en-US-Chirp3-HD-Fenrir", 600_000),
        ("en-US-Wavenet-D", 100),
    ]:
        append_usage_row(
            log,
            timestamp_utc=now,
            chars=chars,
            voice=voice,
            language="en-US",
            audio_format="mp3",
            output_file=tmp_path / "test.mp3",
        )
    snapshot = create_usage_snapshot(log, chars_this_request=100, voice="en-US-Wavenet-D", now_utc=now)
    assert snapshot.voice_family == "Wavenet"

    chirp = snapshot.month_to_date_by_family["Chirp3-HD"]
    assert chirp.chars == 1_100_000
    assert chirp.billable_chars == 100_000
    assert chirp.estimated_cost_usd == 3.0  # 100k * $30/1M

    wavenet = snapshot.month_to_date_by_family["Wavenet"]
    assert wavenet.chars == 100
    assert wavenet.billable_chars == 0
    assert wavenet.estimated_cost_usd == 0.0
