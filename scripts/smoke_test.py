from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a sample Messenger payload to a deployed webhook.")
    parser.add_argument("--base-url", required=True, help="Example: https://example.com")
    parser.add_argument("--payload", default="sample_payloads/message.json")
    args = parser.parse_args()
    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    response = httpx.post(f"{args.base_url.rstrip('/')}/webhook", json=payload, timeout=15)
    print(response.status_code)
    print(response.text)
    response.raise_for_status()


if __name__ == "__main__":
    main()
