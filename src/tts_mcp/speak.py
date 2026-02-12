#!/usr/bin/env python3

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from tts_mcp.core.auth import create_tts_client
from tts_mcp.core.synth import AUDIO_ENCODINGS, SynthesisRequest, read_text_input, synthesize_to_file
from tts_mcp.core.usage import append_usage_row, create_usage_snapshot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Google Cloud TTS local tool")
    parser.add_argument("--text", help="Text to synthesize. If omitted, reads stdin.")
    parser.add_argument("--text-file", default="", help="Path to a UTF-8 text file to synthesize.")
    parser.add_argument("--ssml", action="store_true", help="Treat input as SSML.")
    parser.add_argument("--voice", default="en-US-Chirp3-HD-Fenrir", help="Voice name.")
    parser.add_argument("--language", default="en-US", help="Language code.")
    parser.add_argument(
        "--model",
        default="",
        help="Optional model name (for example models/chirp3-hd).",
    )
    parser.add_argument("--format", choices=sorted(AUDIO_ENCODINGS.keys()), default="mp3")
    parser.add_argument("--speaking-rate", type=float, default=1.0)
    parser.add_argument("--pitch", type=float, default=0.0)
    parser.add_argument("--out", default="", help="Output file path.")
    parser.add_argument(
        "--usage-log",
        default="usage_log.csv",
        help="CSV log path for character usage tracking.",
    )
    return parser.parse_args()


def _resolve_output_path(args: argparse.Namespace) -> Path:
    if args.out:
        return Path(args.out).expanduser().resolve()
    now = datetime.now(UTC)
    stamp = now.strftime("%Y-%m-%d-%H-%M-%S") + f"-{now.microsecond // 1000:03d}"
    return Path(f"{stamp}.{args.format}").resolve()


def main() -> None:
    args = parse_args()
    if not args.text and not args.text_file:
        args.text = input("Paste text and press Enter: ").strip()

    try:
        text = read_text_input(text=args.text or "", text_file=args.text_file)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    if not text:
        raise SystemExit("No input text provided.")

    try:
        client = create_tts_client()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    request = SynthesisRequest(
        text=text,
        ssml=args.ssml,
        voice=args.voice,
        language=args.language,
        model=args.model,
        audio_format=args.format,
        speaking_rate=args.speaking_rate,
        pitch=args.pitch,
        output_file=_resolve_output_path(args),
    )

    try:
        result = synthesize_to_file(client, request)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    now = datetime.now(UTC)
    usage_log = Path(args.usage_log).expanduser().resolve()

    append_usage_row(
        usage_log,
        timestamp_utc=now,
        chars=result.chars,
        voice=result.voice,
        language=result.language,
        audio_format=result.audio_format,
        output_file=result.output_file,
    )

    snapshot = create_usage_snapshot(usage_log, chars_this_request=result.chars, voice=result.voice, now_utc=now)

    print(f"Wrote audio: {result.output_file}")
    print(f"Characters this request: {result.chars}")
    print(f"Voice: {result.voice}")
    if result.model:
        print(f"Model: {result.model}")
    family_usage = snapshot.month_to_date_by_family.get(snapshot.voice_family)
    if family_usage:
        fam = snapshot.voice_family
        print(f"Month-to-date ({fam}): {family_usage.chars:,} chars (free tier: {family_usage.free_tier:,})")
    if args.ssml:
        print("Note: SSML billing can differ slightly from plain character counting.")


if __name__ == "__main__":
    main()
