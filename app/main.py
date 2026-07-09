from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from app.ai_reply import generate_ai_reply
from app.config import get_settings
from app.meta_client import MessengerSendError, send_text_message
from app.rule_engine import choose_reply
from app.security import verify_meta_signature

app = FastAPI(
    title="Messenger Auto Reply Bot",
    description="Facebook Messenger Platform webhook for automatic Page replies.",
    version="0.1.0",
)

logger = logging.getLogger(__name__)


def _iter_messaging_events(payload: dict[str, Any]):
    for entry in payload.get("entry", []) or []:
        for event in entry.get("messaging", []) or []:
            yield event


def _message_text(event: dict[str, Any]) -> str | None:
    message = event.get("message") or {}
    if message.get("is_echo"):
        return None
    text = message.get("text")
    return text if isinstance(text, str) and text.strip() else None


async def _build_reply(message_text: str) -> str:
    settings = get_settings()
    ai_reply = await generate_ai_reply(message_text, settings)
    if ai_reply:
        return ai_reply
    return choose_reply(message_text, settings=settings)


@app.get("/health")
async def health() -> dict[str, Any]:
    settings = get_settings()
    return {
        "ok": True,
        "service": "messenger-auto-reply-bot",
        "auto_reply_enabled": settings.auto_reply_enabled,
        "auto_reply_mode": settings.auto_reply_mode,
        "graph_api_version": settings.graph_api_version,
        "page_access_token_configured": settings.has_page_access_token,
        "app_secret_configured": settings.has_app_secret,
    }


@app.get("/webhook")
async def verify_webhook(request: Request) -> PlainTextResponse:
    settings = get_settings()
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == settings.verify_token and challenge is not None:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@app.post("/webhook")
async def receive_webhook(request: Request) -> JSONResponse:
    settings = get_settings()
    raw_body = await request.body()
    signature = request.headers.get("x-hub-signature-256")
    if not verify_meta_signature(settings.app_secret, raw_body, signature):
        raise HTTPException(status_code=403, detail="Invalid Meta webhook signature")
    try:
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    received = 0
    replied = 0
    skipped = 0
    errors: list[str] = []

    for event in _iter_messaging_events(payload):
        received += 1
        sender_id = (event.get("sender") or {}).get("id")
        text = _message_text(event)
        if not sender_id or not text:
            skipped += 1
            continue
        if not settings.auto_reply_enabled:
            skipped += 1
            continue
        reply_text = await _build_reply(text)
        try:
            await send_text_message(sender_id, reply_text, settings=settings)
            replied += 1
        except MessengerSendError as exc:
            logger.exception("Failed to send Messenger reply")
            errors.append(str(exc))

    return JSONResponse({"ok": not errors, "received": received, "replied": replied, "skipped": skipped, "errors": errors})
