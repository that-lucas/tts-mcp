#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create OAuth user credentials for Google TTS")
    parser.add_argument(
        "--client-secret-file",
        required=True,
        help="Path to OAuth client secret JSON downloaded from Google Cloud.",
    )
    parser.add_argument(
        "--out",
        default="~/.config/gcp/tts-oauth-user.json",
        help="Where to write authorized_user JSON credentials.",
    )
    parser.add_argument(
        "--quota-project",
        default="",
        help="Optional quota project id for billing/quota attribution.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client_secret_file = Path(args.client_secret_file).expanduser().resolve()
    out_file = Path(args.out).expanduser().resolve()

    if not client_secret_file.exists():
        raise SystemExit(f"Client secret file not found: {client_secret_file}")

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_file), SCOPES)
    creds = flow.run_local_server(
        port=0,
        prompt="consent",
        access_type="offline",
        include_granted_scopes="true",
    )

    if not creds.refresh_token:
        raise SystemExit("OAuth did not return a refresh token. Re-run and ensure consent is granted.")

    payload = {
        "type": "authorized_user",
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "refresh_token": creds.refresh_token,
    }
    if args.quota_project:
        payload["quota_project_id"] = args.quota_project

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote OAuth user credentials: {out_file}")
    print("Set this before running speak.py:")
    print(f'export GOOGLE_APPLICATION_CREDENTIALS="{out_file}"')


if __name__ == "__main__":
    main()
