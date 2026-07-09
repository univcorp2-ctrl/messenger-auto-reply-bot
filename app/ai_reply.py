from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


def _extract_output_text(data: dict[str, Any]) -> str | None:
    if isinstance(data.get("output_text"), str):
        return data["output_text"].strip()
    chunks: list[str] = []
    for output in data.get("output", []) or []:
        for content in output.get("content", []) or []:
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    merged = "".join(chunks).strip()
    return merged or None


async def generate_ai_reply(message_text: str, settings: Settings) -> str | None:
    """Generate an optional AI reply with the OpenAI Responses API."""
    if not settings.ai_reply_enabled:
        return None
    payload = {
        "model": settings.openai_model,
        "input": [
            {"role": "system", "content": settings.openai_system_prompt},
            {"role": "user", "content": message_text},
        ],
    }
    headers = {"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post("https://api.openai.com/v1/responses", json=payload, headers=headers)
            response.raise_for_status()
            return _extract_output_text(response.json())
    except httpx.HTTPError as exc:
        logger.warning("OpenAI reply generation failed: %s", exc)
        return None
