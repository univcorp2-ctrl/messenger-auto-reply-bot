from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class MessengerSendError(RuntimeError):
    """Raised when Messenger Send API returns an error."""


async def send_text_message(recipient_id: str, text: str, settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    if not settings.has_page_access_token:
        logger.info("PAGE_ACCESS_TOKEN is not configured. Skipping Messenger send.")
        return {"skipped": True, "reason": "PAGE_ACCESS_TOKEN not configured"}
    payload = {
        "messaging_type": "RESPONSE",
        "recipient": {"id": recipient_id},
        "message": {"text": text},
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            settings.messenger_endpoint,
            params={"access_token": settings.page_access_token},
            json=payload,
        )
    if response.status_code >= 400:
        raise MessengerSendError(f"Messenger Send API failed: {response.status_code} {response.text}")
    return response.json()
