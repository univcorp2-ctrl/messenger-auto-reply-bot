from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _signature(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_health(monkeypatch: Any) -> None:
    monkeypatch.setenv("PAGE_ACCESS_TOKEN", "")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_verify_webhook_success(monkeypatch: Any) -> None:
    monkeypatch.setenv("VERIFY_TOKEN", "token-123")
    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "token-123",
            "hub.challenge": "challenge-value",
        },
    )
    assert response.status_code == 200
    assert response.text == "challenge-value"


def test_verify_webhook_rejects_bad_token(monkeypatch: Any) -> None:
    monkeypatch.setenv("VERIFY_TOKEN", "token-123")
    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong",
            "hub.challenge": "challenge-value",
        },
    )
    assert response.status_code == 403


def test_receive_webhook_replies(monkeypatch: Any, tmp_path: Any) -> None:
    secret = "app-secret"
    monkeypatch.setenv("APP_SECRET", secret)
    monkeypatch.setenv("PAGE_ACCESS_TOKEN", "")
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(
        json.dumps({"rules": [{"name": "default", "pattern": ".*", "response": "ok reply"}]}),
        encoding="utf-8",
    )
    monkeypatch.setenv("REPLY_RULES_PATH", str(rules_path))
    sent: list[tuple[str, str]] = []

    async def fake_send_text_message(
        recipient_id: str,
        text: str,
        settings: Any = None,
    ) -> dict[str, bool]:
        sent.append((recipient_id, text))
        return {"ok": True}

    monkeypatch.setattr("app.main.send_text_message", fake_send_text_message)
    payload = {
        "object": "page",
        "entry": [
            {
                "id": "PAGE_ID",
                "messaging": [
                    {
                        "sender": {"id": "USER_ID"},
                        "recipient": {"id": "PAGE_ID"},
                        "message": {"text": "hello"},
                    }
                ],
            }
        ],
    }
    body = json.dumps(payload).encode("utf-8")
    response = client.post(
        "/webhook",
        content=body,
        headers={
            "X-Hub-Signature-256": _signature(secret, body),
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 200
    assert response.json()["replied"] == 1
    assert sent == [("USER_ID", "ok reply")]


def test_receive_webhook_rejects_invalid_signature(monkeypatch: Any) -> None:
    monkeypatch.setenv("APP_SECRET", "app-secret")
    response = client.post(
        "/webhook",
        json={"entry": []},
        headers={"X-Hub-Signature-256": "sha256=bad"},
    )
    assert response.status_code == 403
