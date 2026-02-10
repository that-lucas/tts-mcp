from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass
class UsageSnapshot:
    chars_this_request: int
    month_key: str
    month_to_date_chars: int


def append_usage_row(
    log_path: Path,
    *,
    timestamp_utc: datetime,
    chars: int,
    voice: str,
    language: str,
    audio_format: str,
    output_file: Path,
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    has_file = log_path.exists()
    with log_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "timestamp_utc",
                "month",
                "chars",
                "voice",
                "language",
                "format",
                "output_file",
            ],
        )
        if not has_file:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp_utc": timestamp_utc.isoformat(),
                "month": timestamp_utc.strftime("%Y-%m"),
                "chars": str(chars),
                "voice": voice,
                "language": language,
                "format": audio_format,
                "output_file": str(output_file),
            }
        )


def month_total_chars(log_path: Path, month_key: str) -> int:
    if not log_path.exists():
        return 0

    total = 0
    with log_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("month") == month_key:
                total += int(row["chars"])
    return total


def create_usage_snapshot(log_path: Path, *, chars_this_request: int, now_utc: datetime) -> UsageSnapshot:
    month_key = now_utc.strftime("%Y-%m")
    month_chars = month_total_chars(log_path, month_key)
    return UsageSnapshot(
        chars_this_request=chars_this_request,
        month_key=month_key,
        month_to_date_chars=month_chars,
    )
