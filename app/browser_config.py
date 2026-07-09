from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SELECTOR_SEPARATOR = "||"


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _as_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _split_selectors(value: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if not value:
        return default
    selectors = tuple(item.strip() for item in value.split(SELECTOR_SEPARATOR) if item.strip())
    return selectors or default


@dataclass(frozen=True)
class BrowserSelectors:
    thread_selectors: tuple[str, ...]
    message_text_selectors: tuple[str, ...]
    composer_selectors: tuple[str, ...]
    send_button_selectors: tuple[str, ...]


@dataclass(frozen=True)
class BrowserBotSettings:
    inbox_url: str
    user_data_dir: Path
    headless: bool
    poll_seconds: float
    max_replies_per_run: int
    dry_run: bool
    reply_rules_path: str
    login_wait_seconds: int


DEFAULT_THREAD_SELECTORS = (
    'div[aria-label*="未読"]',
    'div[aria-label*="Unread"]',
    '[role="row"][aria-label*="未読"]',
    '[role="row"][aria-label*="Unread"]',
)
DEFAULT_MESSAGE_TEXT_SELECTORS = (
    '[data-testid="message-container"] [dir="auto"]',
    '[role="main"] [dir="auto"]',
)
DEFAULT_COMPOSER_SELECTORS = (
    'div[role="textbox"][contenteditable="true"][aria-label*="メッセージ"]',
    'div[role="textbox"][contenteditable="true"][aria-label*="Message"]',
    'div[role="textbox"][contenteditable="true"]',
)
DEFAULT_SEND_BUTTON_SELECTORS = (
    'div[aria-label="送信"]',
    'div[aria-label="Send"]',
    '[data-testid="send"]',
)


def get_browser_selectors() -> BrowserSelectors:
    return BrowserSelectors(
        thread_selectors=_split_selectors(
            os.getenv("UI_BOT_THREAD_SELECTORS"),
            DEFAULT_THREAD_SELECTORS,
        ),
        message_text_selectors=_split_selectors(
            os.getenv("UI_BOT_MESSAGE_TEXT_SELECTORS"),
            DEFAULT_MESSAGE_TEXT_SELECTORS,
        ),
        composer_selectors=_split_selectors(
            os.getenv("UI_BOT_COMPOSER_SELECTORS"),
            DEFAULT_COMPOSER_SELECTORS,
        ),
        send_button_selectors=_split_selectors(
            os.getenv("UI_BOT_SEND_BUTTON_SELECTORS"),
            DEFAULT_SEND_BUTTON_SELECTORS,
        ),
    )


def get_browser_bot_settings() -> BrowserBotSettings:
    return BrowserBotSettings(
        inbox_url=os.getenv("UI_BOT_INBOX_URL", "https://www.facebook.com/messages/t/"),
        user_data_dir=Path(os.getenv("UI_BOT_USER_DATA_DIR", ".playwright/facebook-profile")),
        headless=_as_bool(os.getenv("UI_BOT_HEADLESS"), False),
        poll_seconds=_as_float(os.getenv("UI_BOT_POLL_SECONDS"), 5.0),
        max_replies_per_run=_as_int(os.getenv("UI_BOT_MAX_REPLIES_PER_RUN"), 10),
        dry_run=_as_bool(os.getenv("UI_BOT_DRY_RUN"), True),
        reply_rules_path=os.getenv("UI_BOT_REPLY_RULES_PATH", "config/reply_rules.example.json"),
        login_wait_seconds=_as_int(os.getenv("UI_BOT_LOGIN_WAIT_SECONDS"), 60),
    )
