"""Signature-verified platform webhooks updating post status.

Each platform signs webhook payloads; we verify with HMAC-SHA256 using a
per-platform shared secret before trusting the status update. Failed
verification raises and is never applied.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time

# platform -> shared secret (use env in prod; tests pass explicit secrets)
SHARED_SECRETS = {
    "facebook_feed": "fb_webhook_secret_dev",
    "twitter_card": "tw_webhook_secret_dev",
}


class SignatureError(Exception):
    pass


def sign(platform: str, payload: dict, timestamp: int | None = None) -> str:
    secret = SHARED_SECRETS[platform].encode("utf-8")
    ts = timestamp or int(time.time())
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    mac = hmac.new(secret, f"{ts}.".encode("utf-8") + body, hashlib.sha256).hexdigest()
    return f"t={ts},sha256={mac}"


def verify_and_apply(platform: str, payload: dict, signature: str, event_handler) -> dict:
    """Verify HMAC then apply the status update via event_handler."""
    _verify(platform, payload, signature)
    return event_handler(platform, payload)


def _verify(platform: str, payload: dict, signature: str) -> None:
    if platform not in SHARED_SECRETS:
        raise SignatureError(f"unknown platform: {platform}")
    try:
        ts_part, mac_part = signature.split(",", 1)
        ts = int(ts_part.split("=", 1)[1])
        provided = mac_part.split("=", 1)[1]
    except (ValueError, IndexError) as exc:
        raise SignatureError("malformed signature") from exc
    # tolerate clock skew up to 5 min
    if abs(time.time() - ts) > 300:
        raise SignatureError("signature timestamp too old")
    expected = sign(platform, payload, ts).split(",", 1)[1].split("=", 1)[1]
    if not hmac.compare_digest(provided, expected):
        raise SignatureError("signature mismatch")
