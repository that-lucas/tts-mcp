#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

from tts_core.auth import create_tts_client
from tts_core.synth import SynthesisRequest, read_text_input, sanitize_filename, synthesize_to_file
from tts_core.voices import list_voices

AUDIO_FORMATS = ["mp3", "wav", "ogg"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate TTS audio for many US voices")
    parser.add_argument("--text-file", required=True, help="UTF-8 text file to synthesize")
    parser.add_argument("--out-dir", default="./out", help="Output directory")
    parser.add_argument(
        "--families",
        default="Chirp3,Neural2",
        help="Comma-separated family filters (for example Chirp3,Neural2)",
    )
    parser.add_argument("--language", default="en-US", help="Language filter")
    parser.add_argument("--format", choices=AUDIO_FORMATS, default="mp3")
    parser.add_argument("--speaking-rate", type=float, default=1.0)
    parser.add_argument("--pitch", type=float, default=0.0)
    parser.add_argument("--limit", type=int, default=0, help="Optional max voices (0 means all)")
    return parser.parse_args()


def model_tag_and_name(voice_name: str) -> tuple[str, str]:
    lower_name = voice_name.lower()
    if "wave" in lower_name and "net" in lower_name:
        return "wavenet", ""
    if "neural2" in lower_name:
        return "neural2", ""
    if "chirp3" in lower_name:
        return "chirp3", "models/chirp3-hd"
    return "generic", ""


def main() -> None:
    args = parse_args()
    try:
        text = read_text_input(text="", text_file=args.text_file)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    families = [part.strip().lower() for part in args.families.split(",") if part.strip()]
    language = args.language.strip()

    try:
        client = create_tts_client()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    selected = list_voices(client, language=language, family="", limit=0)
    selected = [row for row in selected if not families or any(f in row.name.lower() for f in families)]
    if args.limit > 0:
        selected = selected[: args.limit]

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating {len(selected)} files in {out_dir}")
    failures = 0

    for voice in selected:
        tag, model_name = model_tag_and_name(voice.name)
        filename = f"{tag}-{sanitize_filename(voice.name)}.{args.format}"
        output_path = out_dir / filename

        try:
            synthesize_to_file(
                client,
                SynthesisRequest(
                    text=text,
                    ssml=False,
                    voice=voice.name,
                    language=language,
                    model=model_name,
                    audio_format=args.format,
                    speaking_rate=args.speaking_rate,
                    pitch=args.pitch,
                    output_file=output_path,
                ),
            )
            print(f"ok   {output_path.name}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"fail {voice.name}: {exc}")

    print(f"Done. Success: {len(selected) - failures}, Failed: {failures}")


if __name__ == "__main__":
    main()
