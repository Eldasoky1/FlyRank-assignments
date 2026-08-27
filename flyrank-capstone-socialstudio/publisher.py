"""SocialPublisher: platform adapters + idempotent publish + 429 backoff.

Two adapters (Facebook, Twitter/X) implement a common SocialPublisher
interface. publish() is idempotent: the same content hash sent to the same
platform within an idempotency window returns the already-created external id
without double-posting. A 429/Retry-After response backs off with the server's
retry delay.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time


def content_hash(text: str, assets: list[str] | None = None) -> str:
    payload = hashlib.sha256((text + "|" + json.dumps(assets or [])).encode("utf-8"))
    return payload.hexdigest()[:16]


class PublishResult:
    def __init__(self, external_id, platform, status, reason="", retried=0):
        self.external_id = external_id
        self.platform = platform
        self.status = status
        self.reason = reason
        self.retried = retried

    def to_dict(self):
        return {
            "external_id": self.external_id,
            "platform": self.platform,
            "status": self.status,
            "reason": self.reason,
            "retried": self.retried,
        }


class HTTPError(Exception):
    def __init__(self, status, retry_after=None, body=""):
        super().__init__(f"HTTP {status}: {body}")
        self.status = status
        self.retry_after = retry_after
        self.body = body


class SocialPublisher:
    """Interface implemented by concrete adapters."""

    platform = "base"
    max_retries = 3

    def send(self, account_oauth: dict, content: dict) -> PublishResult:
        raise NotImplementedError


class MockTransport:
    """In-memory HTTP-like transport so adapters run offline in tests."""

    def __init__(self, always_ok=True, fail_once=False, rate_limited=False):
        self.calls = []
        self.always_ok = always_ok
        self.fail_once = fail_once
        self.rate_limited = rate_limited
        self.external_counter = 0

    def post(self, url, json_body, headers):
        self.calls.append((url, json_body, headers))
        if self.rate_limited:
            return {"status": 429, "retry_after": 2, "body": "rate limited"}
        if self.fail_once and self.external_counter == 0:
            return {"status": 500, "body": "server error"}
        self.external_counter += 1
        return {"status": 201, "body": "", "external_id": f"{self.external_counter:08d}"}


class FacebookPublisher(SocialPublisher):
    platform = "facebook_feed"

    def __init__(self, transport=None):
        self.transport = transport or MockTransport()

    def send(self, account_oauth, content):
        h = content_hash(content["text"], content.get("assets"))
        external_id = _idempotent_lookup(self.platform, h)
        if external_id:
            return PublishResult(external_id, self.platform, "already_published", reason="idempotent")
        resp = self._post_with_backoff(self._build_payload(account_oauth, content))
        ext = _record_idempotent(self.platform, h, resp["external_id"])
        return PublishResult(ext, self.platform, "published")

    def _build_payload(self, oauth, content):
        return {"page_id": oauth.get("account_id"), "message": content["text"],
                "access_token": oauth.get("access_token"),
                "link": content.get("link") or "", "image": (content.get("assets") or [None])[0]}

    def _post_with_backoff(self, payload):
        retried = 0
        for attempt in range(self.max_retries + 1):
            r = self.transport.post("https://graph.facebook.com/v19/0/me/feed",
                                    payload, {"Authorization": "Bearer x"})
            if r["status"] == 429:
                delay = r.get("retry_after", 1)
                time.sleep(delay)
                retried += 1
                continue
            if 500 <= r["status"] < 600 and attempt < self.max_retries:
                time.sleep(0.02 * (attempt + 1))
                retried += 1
                continue
            if r["status"] >= 400:
                raise HTTPError(r["status"], r.get("retry_after"), r.get("body", ""))
            return r
        raise HTTPError(429, r.get("retry_after"), "gave up after retries")


class TwitterPublisher(SocialPublisher):
    platform = "twitter_card"

    def __init__(self, transport=None):
        self.transport = transport or MockTransport()

    def send(self, account_oauth, content):
        h = content_hash(content["text"], content.get("assets"))
        external_id = _idempotent_lookup(self.platform, h)
        if external_id:
            return PublishResult(external_id, self.platform, "already_published", reason="idempotent")
        r = self._post_with_backoff(self._build_payload(account_oauth, content))
        ext = _record_idempotent(self.platform, h, r["external_id"])
        return PublishResult(ext, self.platform, "published")

    def _build_payload(self, oauth, content):
        return {"text": content["text"], "media": (content.get("assets") or [])}

    def _post_with_backoff(self, payload):
        for attempt in range(self.max_retries + 1):
            r = self.transport.post("https://api.twitter.com/2/tweets", payload, {"Authorization": "Bearer x"})
            if r["status"] == 429:
                time.sleep(r.get("retry_after", 1))
                continue
            if 500 <= r["status"] < 600 and attempt < self.max_retries:
                time.sleep(0.02 * (attempt + 1))
                continue
            if r["status"] >= 400:
                raise HTTPError(r["status"], r.get("retry_after"), r.get("body", ""))
            return r
        raise HTTPError(429, r.get("retry_after"), "gave up")


# --- idempotency bookkeeping (module-level; mirrors DB unique constraint) ---
_IDEM = {}
_IDEM_LOCK = threading.Lock()


def _idempotent_lookup(platform, h):
    with _IDEM_LOCK:
        return _IDEM.get((platform, h))


def _record_idempotent(platform, h, external_id):
    with _IDEM_LOCK:
        _IDEM[(platform, h)] = external_id
    return external_id
