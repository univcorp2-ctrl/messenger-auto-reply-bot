from __future__ import annotations

import argparse
import asyncio
import logging
from dataclasses import replace
from pathlib import Path

from app.browser_config import get_browser_bot_settings, get_browser_selectors
from app.browser_messenger_bot import run_browser_bot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a Playwright browser UI bot for Facebook Messenger replies.",
    )
    parser.add_argument("--once", action="store_true", help="Process at most one unread thread.")
    parser.add_argument("--login-only", action="store_true", help="Open browser for manual login only.")
    parser.add_argument("--send", action="store_true", help="Actually send replies. Default is dry-run.")
    parser.add_argument("--headless", action="store_true", help="Run Chromium headless after login is saved.")
    parser.add_argument("--inbox-url", help="Messenger or Business Suite inbox URL to open.")
    parser.add_argument("--user-data-dir", help="Persistent Playwright profile directory.")
    parser.add_argument("--max-replies", type=int, help="Maximum replies in one run.")
    return parser.parse_args()


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()
    settings = get_browser_bot_settings()

    if args.send:
        settings = replace(settings, dry_run=False)
    if args.headless:
        settings = replace(settings, headless=True)
    if args.inbox_url:
        settings = replace(settings, inbox_url=args.inbox_url)
    if args.user_data_dir:
        settings = replace(settings, user_data_dir=Path(args.user_data_dir))
    if args.max_replies is not None:
        settings = replace(settings, max_replies_per_run=args.max_replies)

    selectors = get_browser_selectors()
    results = await run_browser_bot(settings, selectors, once=args.once, login_only=args.login_only)
    for result in results:
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
