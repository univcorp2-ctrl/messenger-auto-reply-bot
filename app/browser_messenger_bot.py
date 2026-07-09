from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, replace
from typing import Any

from app.browser_config import BrowserBotSettings, BrowserSelectors
from app.config import get_settings
from app.rule_engine import choose_reply

logger = logging.getLogger(__name__)


class UiAutomationError(RuntimeError):
    """Raised when the browser UI cannot be controlled safely."""


@dataclass(frozen=True)
class BrowserReplyResult:
    ok: bool
    sent: bool
    dry_run: bool
    incoming_text: str
    reply_text: str
    reason: str


async def _first_visible_locator(
    page: Any,
    selectors: tuple[str, ...],
    timeout_ms: int = 500,
) -> Any | None:
    for selector in selectors:
        try:
            locator = page.locator(selector).first()
            if await locator.count() == 0:
                continue
            if await locator.is_visible(timeout=timeout_ms):
                return locator
        except Exception as exc:  # noqa: BLE001 - UI automation must continue through stale selectors.
            logger.debug("Selector failed: %s (%s)", selector, exc)
    return None


async def _latest_visible_text(
    page: Any,
    selectors: tuple[str, ...],
    max_nodes: int = 20,
) -> str:
    for selector in selectors:
        try:
            locator = page.locator(selector)
            count = min(await locator.count(), max_nodes)
            for index in range(count - 1, -1, -1):
                text = await locator.nth(index).inner_text(timeout=500)
                cleaned = " ".join(text.split())
                if cleaned:
                    return cleaned
        except Exception as exc:  # noqa: BLE001
            logger.debug("Message text selector failed: %s (%s)", selector, exc)
    return ""


async def click_first_unread_thread(page: Any, selectors: BrowserSelectors) -> bool:
    thread = await _first_visible_locator(page, selectors.thread_selectors, timeout_ms=800)
    if thread is None:
        return False
    await thread.click()
    await page.wait_for_timeout(800)
    return True


async def build_reply_text(incoming_text: str, reply_rules_path: str) -> str:
    settings = replace(get_settings(), reply_rules_path=reply_rules_path)
    return choose_reply(incoming_text, settings=settings)


async def send_reply_to_current_thread(
    page: Any,
    reply_text: str,
    selectors: BrowserSelectors,
    dry_run: bool,
) -> BrowserReplyResult:
    composer = await _first_visible_locator(page, selectors.composer_selectors, timeout_ms=1200)
    if composer is None:
        raise UiAutomationError("Message composer was not found. Update UI_BOT_COMPOSER_SELECTORS.")

    if dry_run:
        return BrowserReplyResult(
            ok=True,
            sent=False,
            dry_run=True,
            incoming_text="",
            reply_text=reply_text,
            reason="dry_run",
        )

    await composer.click()
    await composer.fill(reply_text)

    send_button = await _first_visible_locator(page, selectors.send_button_selectors, timeout_ms=500)
    if send_button is not None:
        await send_button.click()
    else:
        await composer.press("Enter")

    await page.wait_for_timeout(300)
    return BrowserReplyResult(
        ok=True,
        sent=True,
        dry_run=False,
        incoming_text="",
        reply_text=reply_text,
        reason="sent",
    )


async def reply_once_from_browser_page(
    page: Any,
    settings: BrowserBotSettings,
    selectors: BrowserSelectors,
) -> BrowserReplyResult:
    opened = await click_first_unread_thread(page, selectors)
    if not opened:
        return BrowserReplyResult(
            ok=True,
            sent=False,
            dry_run=settings.dry_run,
            incoming_text="",
            reply_text="",
            reason="no_unread_thread_found",
        )

    incoming_text = await _latest_visible_text(page, selectors.message_text_selectors)
    if not incoming_text:
        return BrowserReplyResult(
            ok=False,
            sent=False,
            dry_run=settings.dry_run,
            incoming_text="",
            reply_text="",
            reason="incoming_message_text_not_found",
        )

    reply_text = await build_reply_text(incoming_text, settings.reply_rules_path)
    result = await send_reply_to_current_thread(page, reply_text, selectors, settings.dry_run)
    return replace(result, incoming_text=incoming_text)


async def run_browser_bot(
    settings: BrowserBotSettings,
    selectors: BrowserSelectors,
    once: bool = False,
    login_only: bool = False,
) -> list[BrowserReplyResult]:
    """Run the Playwright UI bot with a persistent browser profile.

    This does not read access tokens, bypass login, solve CAPTCHA, or bypass 2FA.
    The first run should be non-headless so the operator can sign in manually.
    """

    from playwright.async_api import async_playwright

    settings.user_data_dir.mkdir(parents=True, exist_ok=True)
    results: list[BrowserReplyResult] = []

    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=settings.user_data_dir,
            headless=settings.headless,
            viewport={"width": 1440, "height": 1000},
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(settings.inbox_url, wait_until="domcontentloaded")

        if login_only:
            logger.info("Login-only mode. Complete login in the opened browser window.")
            await page.wait_for_timeout(settings.login_wait_seconds * 1000)
            await context.close()
            return results

        for _ in range(settings.max_replies_per_run):
            result = await reply_once_from_browser_page(page, settings, selectors)
            results.append(result)
            logger.info("Browser reply result: %s", result)
            if once or result.reason == "no_unread_thread_found":
                break
            await asyncio.sleep(settings.poll_seconds)

        await context.close()
    return results
