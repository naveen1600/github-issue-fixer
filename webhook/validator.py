from __future__ import annotations

import hashlib
import hmac

from fastapi import HTTPException, Request

from config import config


async def verify_github_signature(request: Request) -> bytes:
    body = await request.body()
    sig_header = request.headers.get("X-Hub-Signature-256", "")

    if not sig_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Missing or malformed X-Hub-Signature-256")

    expected = "sha256=" + hmac.new(
        config.github_webhook_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, sig_header):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    return body
