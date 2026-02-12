#!/usr/bin/env python3

from __future__ import annotations

import argparse

from tts_mcp.core.auth import create_tts_client
from tts_mcp.core.voices import list_voices


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List Google TTS voices")
    parser.add_argument("--language", default="", help="Optional language filter, for example en-US")
    parser.add_argument("--family", default="", help="Optional voice family filter")
    parser.add_argument("--limit", type=int, default=0, help="Optional limit")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        client = create_tts_client()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    rows = list_voices(client, language=args.language, family=args.family, limit=args.limit)

    for row in rows:
        print(f"{row.name}\t{','.join(row.language_codes)}")

    print(f"\nTotal voices: {len(rows)}")


if __name__ == "__main__":
    main()
