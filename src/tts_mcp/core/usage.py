from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

VOICE_FAMILIES: dict[str, dict] = {
    "Chirp3-HD": {"rate_per_million": 30, "free_chars": 1_000_000},
    "Chirp-HD": {"rate_per_million": 30, "free_chars": 1_000_000},
    "Studio": {"rate_per_million": 160, "free_chars": 1_000_000},
    "Neural2": {"rate_per_million": 16, "free_chars": 1_000_000},
    "News": {"rate_per_million": 16, "free_chars": 1_000_000},
    "Casual": {"rate_per_million": 16, "free_chars": 1_000_000},
    "Polyglot": {"rate_per_million": 16, "free_chars": 1_000_000},
    "Wavenet": {"rate_per_million": 4, "free_chars": 4_000_000},
    "Standard": {"rate_per_million": 4, "free_chars": 4_000_000},
}


def detect_family(voice: str) -> str:
    """Extract the voice family from a voice name like 'en-US-Chirp3-HD-Fenrir'."""
    for family in VOICE_FAMILIES:
        if family in voice:
            return family
    return "Unknown"


@dataclass
class FamilyUsage:
    chars: int
    free_tier: int
    rate_per_million: int

    @property
    def billable_chars(self) -> int:
        return max(0, self.chars - self.free_tier)

    @property
    def estimated_cost_usd(self) -> float:
        return self.billable_chars * self.rate_per_million / 1_000_000


@dataclass
class UsageSnapshot:
    chars_this_request: int
    voice_family: str
    month_key: str
    month_to_date_by_family: dict[str, FamilyUsage] = field(default_factory=dict)


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


def month_chars_by_family(log_path: Path, month_key: str) -> dict[str, int]:
    """Sum characters per voice family for a given month."""
    if not log_path.exists():
        return {}

    totals: dict[str, int] = {}
    with log_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("month") == month_key:
                family = detect_family(row.get("voice", ""))
                totals[family] = totals.get(family, 0) + int(row["chars"])
    return totals


def create_usage_snapshot(log_path: Path, *, chars_this_request: int, voice: str, now_utc: datetime) -> UsageSnapshot:
    month_key = now_utc.strftime("%Y-%m")
    family = detect_family(voice)
    by_family_chars = month_chars_by_family(log_path, month_key)

    by_family: dict[str, FamilyUsage] = {}
    for fam, chars in sorted(by_family_chars.items()):
        info = VOICE_FAMILIES.get(fam, {"rate_per_million": 0, "free_chars": 0})
        by_family[fam] = FamilyUsage(
            chars=chars,
            free_tier=info["free_chars"],
            rate_per_million=info["rate_per_million"],
        )

    return UsageSnapshot(
        chars_this_request=chars_this_request,
        voice_family=family,
        month_key=month_key,
        month_to_date_by_family=by_family,
    )
