from __future__ import annotations

import hashlib
import hmac


def verify_meta_signature(app_secret: str, raw_body: bytes, signature_header: str | None) -> bool:
    """Validate Meta's X-Hub-Signature-256 header.

    Meta sends a header like `sha256=<hex digest>`. If APP_SECRET is not configured,
    local development is allowed and this function returns True.
    """
    if not app_secret:
        return True
    if not signature_header:
        return False
    prefix = "sha256="
    if not signature_header.startswith(prefix):
        return False
    provided = signature_header[len(prefix) :].strip()
    expected = hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(provided, expected)
