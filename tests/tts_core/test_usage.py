from __future__ import annotations

import csv
from datetime import UTC, datetime

from tts_core.usage import append_usage_row, create_usage_snapshot, month_total_chars


def test_append_usage_row_creates_file(tmp_path):
    log = tmp_path / "usage.csv"
    now = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)
    append_usage_row(
        log,
        timestamp_utc=now,
        chars=42,
        voice="v",
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
            voice="v",
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
        voice="v",
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
            voice="v",
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
        voice="v",
        language="en-US",
        audio_format="mp3",
        output_file=tmp_path / "test.mp3",
    )
    assert month_total_chars(log, "2025-01") == 0


def test_create_usage_snapshot(tmp_path):
    log = tmp_path / "usage.csv"
    now = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)
    append_usage_row(
        log,
        timestamp_utc=now,
        chars=50,
        voice="v",
        language="en-US",
        audio_format="mp3",
        output_file=tmp_path / "test.mp3",
    )
    snapshot = create_usage_snapshot(log, chars_this_request=50, now_utc=now)
    assert snapshot.chars_this_request == 50
    assert snapshot.month_key == "2025-06"
    assert snapshot.month_to_date_chars == 50
