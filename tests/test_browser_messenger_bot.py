from __future__ import annotations

import json
from pathlib import Path

import pytest
from playwright.async_api import async_playwright

from app.browser_config import BrowserBotSettings, BrowserSelectors
from app.browser_messenger_bot import build_reply_text, reply_once_from_browser_page


@pytest.mark.asyncio
async def test_build_reply_text_uses_existing_rules(tmp_path: Path) -> None:
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(
        json.dumps(
            {
                "rules": [
                    {"name": "price", "pattern": "料金", "response": "料金テスト返信"},
                    {"name": "default", "pattern": ".*", "response": "default"},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    assert await build_reply_text("料金を教えて", str(rules_path)) == "料金テスト返信"


@pytest.mark.browser
@pytest.mark.asyncio
async def test_playwright_demo_page_can_build_and_send_reply(tmp_path: Path) -> None:
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(
        json.dumps(
            {
                "rules": [
                    {"name": "price", "pattern": "料金", "response": "料金について確認します。"},
                    {"name": "default", "pattern": ".*", "response": "ありがとうございます。"},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    html = """
    <!doctype html>
    <html lang="ja">
      <body>
        <button data-testid="thread" aria-label="Unread conversation">Unread thread</button>
        <main role="main">
          <div data-testid="message-container"><span dir="auto">料金を教えてください</span></div>
        </main>
        <div role="textbox" contenteditable="true" aria-label="Message"></div>
        <button data-testid="send">Send</button>
        <div id="sent"></div>
        <script>
          document.querySelector('[data-testid="send"]').addEventListener('click', () => {
            document.querySelector('#sent').textContent = document.querySelector('[role="textbox"]').innerText;
          });
        </script>
      </body>
    </html>
    """

    selectors = BrowserSelectors(
        thread_selectors=('[data-testid="thread"]',),
        message_text_selectors=('[data-testid="message-container"] [dir="auto"]',),
        composer_selectors=('[role="textbox"]',),
        send_button_selectors=('[data-testid="send"]',),
    )
    settings = BrowserBotSettings(
        inbox_url="about:blank",
        user_data_dir=tmp_path / "profile",
        headless=True,
        poll_seconds=0.1,
        max_replies_per_run=1,
        dry_run=False,
        reply_rules_path=str(rules_path),
        login_wait_seconds=1,
    )

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html)
        result = await reply_once_from_browser_page(page, settings, selectors)
        sent_text = await page.locator("#sent").inner_text()
        await browser.close()

    assert result.ok is True
    assert result.sent is True
    assert result.incoming_text == "料金を教えてください"
    assert result.reply_text == "料金について確認します。"
    assert sent_text == "料金について確認します。"


@pytest.mark.browser
@pytest.mark.asyncio
async def test_playwright_demo_page_dry_run_does_not_send(tmp_path: Path) -> None:
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(
        json.dumps({"rules": [{"name": "default", "pattern": ".*", "response": "dry run reply"}]}),
        encoding="utf-8",
    )
    selectors = BrowserSelectors(
        thread_selectors=('[data-testid="thread"]',),
        message_text_selectors=('[data-testid="message-container"] [dir="auto"]',),
        composer_selectors=('[role="textbox"]',),
        send_button_selectors=('[data-testid="send"]',),
    )
    settings = BrowserBotSettings(
        inbox_url="about:blank",
        user_data_dir=tmp_path / "profile",
        headless=True,
        poll_seconds=0.1,
        max_replies_per_run=1,
        dry_run=True,
        reply_rules_path=str(rules_path),
        login_wait_seconds=1,
    )

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(
            '<button data-testid="thread">Unread</button>'
            '<div data-testid="message-container"><span dir="auto">hello</span></div>'
            '<div role="textbox" contenteditable="true" aria-label="Message"></div>'
            '<button data-testid="send">Send</button>'
            '<div id="sent"></div>'
        )
        result = await reply_once_from_browser_page(page, settings, selectors)
        sent_text = await page.locator("#sent").inner_text()
        await browser.close()

    assert result.ok is True
    assert result.sent is False
    assert result.dry_run is True
    assert result.reply_text == "dry run reply"
    assert sent_text == ""
