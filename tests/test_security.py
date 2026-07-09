from __future__ import annotations

import hashlib
import hmac

from app.security import verify_meta_signature


def test_verify_meta_signature_allows_local_dev_without_secret() -> None:
    assert verify_meta_signature("", b"{}", None) is True


def test_verify_meta_signature_accepts_valid_signature() -> None:
    secret = "test-secret"
    body = b'{"hello":"world"}'
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_meta_signature(secret, body, f"sha256={digest}") is True


def test_verify_meta_signature_rejects_invalid_signature() -> None:
    assert verify_meta_signature("test-secret", b"{}", "sha256=bad") is False
