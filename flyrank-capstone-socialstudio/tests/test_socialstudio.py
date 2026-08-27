"""Tests for the Social Media Studio."""

import json
import os
import tempfile

import pytest

from captions import compose, compose_for
from oauth_store import OAuthStore
from publisher import (FacebookPublisher, HTTPError, MockTransport,
                       PublishResult, TwitterPublisher, content_hash)
from scheduler import Scheduler
from variants import VARIANT_SPECS, make_variants, source_hash, variant_key
from webhooks import SignatureError, sign, verify_and_apply


# ---------------------------------------------------------------------------
# Caption composer
# ---------------------------------------------------------------------------
def test_compose_contains_hook_hashtags():
    text = compose({"brand": "Acme", "product": "widget", "hashtags": ["new drop", "launch"]},
                   "facebook_feed")
    assert "Acme" in text
    assert "#new_drop" in text and "#launch" in text


def test_compose_truncates_to_platform_limit():
    post = {"brand": "B", "product": "x", "body": "y" * 5000}
    cap = compose_for(post, "twitter_card")
    assert cap.length <= 280
    assert cap.text.endswith("…")
    assert cap.platform == "twitter_card"


def test_caption_is_filled_and_platform_model():
    cap = compose_for({"brand": "A", "product": "z"}, "facebook_feed")
    assert len(cap.text) > 0


# ---------------------------------------------------------------------------
# Image variants
# ---------------------------------------------------------------------------
def _make_source_image(path):
    from PIL import Image

    img = Image.new("RGB", (2000, 1500), (120, 80, 40))
    img.save(path)
    return path


def test_make_variants_produces_platform_sizes(tmp_path):
    src = _make_source_image(str(tmp_path / "src.png"))
    out = str(tmp_path / "out")
    variants = make_variants(src, out, platforms=["instagram_square", "twitter_card"])
    by = {v.platform: v for v in variants}
    assert by["instagram_square"].width == 1080 and by["instagram_square"].height == 1080
    assert by["twitter_card"].width == 1600 and by["twitter_card"].height == 900
    for v in variants:
        assert v.exists and v.size_bytes > 0


def test_variant_key_is_content_addr(tmp_path):
    a = _make_source_image(str(tmp_path / "a.png"))
    k1 = variant_key(a, "twitter_card")
    k2 = variant_key(a, "twitter_card")
    assert k1 == k2
    assert source_hash(a) in k1


# ---------------------------------------------------------------------------
# Encrypted OAuth store
# ---------------------------------------------------------------------------
def test_oauth_roundtrip():
    store = OAuthStore(secret="unit-test-secret")
    store.save("twitter_card", "acct1", {"access_token": "tok_123", "expires": 999})
    assert store.load("twitter_card", "acct1")["access_token"] == "tok_123"


def test_oauth_no_plaintext_and_tamper_detected():
    store = OAuthStore("s")
    store.save("facebook_feed", "acct", {"access_token": "SECRET_VALUE"})
    blob = store._tokens[("facebook_feed", "acct")]
    assert b"SECRET_VALUE" not in blob  # not stored in plaintext
    with pytest.raises(Exception):
        store._fernet.decrypt(blob[:-1] + bytes([blob[-1] ^ 0xFF]))


# ---------------------------------------------------------------------------
# Publisher: idempotency + 429/Retry-After backoff
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _reset_idem():
    from publisher import _IDEM

    _IDEM.clear()
    yield


def test_facebook_publish_is_idempotent():
    p = FacebookPublisher()
    content = {"text": "hello world", "assets": ["a.jpg"]}
    r1 = p.send({"account_id": "p1", "access_token": "t"}, content)
    r2 = p.send({"account_id": "p1", "access_token": "t"}, content)
    assert r1.status == "published" and r2.status == "already_published"
    assert r1.external_id == r2.external_id  # no double post


def test_twitter_publish_works():
    p = TwitterPublisher()
    r = p.send({"account_id": "h"}, {"text": "a tweet", "assets": []})
    assert r.status == "published" and r.external_id


def test_rate_limit_429_backs_off_with_retry_after():
    transport = MockTransport(rate_limited=True)
    p = FacebookPublisher(transport=transport)
    # after max_retries+1 attempts it should raise HTTPError, not double-post

    start = __import__("time").time()
    with pytest.raises(HTTPError) as e:
        p.send({"account_id": "p", "access_token": "t"}, {"text": "x"})
    assert e.value.status == 429
    assert __import__("time").time() - start >= 2  # honored retry-after


def test_publisher_consistent_external_id_for_same_content():
    p = FacebookPublisher()
    c = {"text": "same post", "assets": ["img.png"]}
    r1 = p.send({"account_id": "p"}, c)
    r2 = p.send({"account_id": "p"}, c)
    assert r1.external_id == r2.external_id


# ---------------------------------------------------------------------------
# Durable scheduler (crash-safe, no double post)
# ---------------------------------------------------------------------------
@pytest.fixture
def sched(tmp_path):
    return Scheduler(db_path=str(tmp_path / "social.db"))


def test_scheduler_enqueue_is_idempotent(sched):
    id1, n1 = sched.enqueue("facebook_feed", "post A", "acct")
    id2, n2 = sched.enqueue("facebook_feed", "post A", "acct")
    assert id1 == id2 and n2 == "already_queued"


def test_scheduler_crash_recovery_reclaims_stale_running(sched):
    job_id, _ = sched.enqueue("twitter_card", "post B", "acct")
    # simulate crash: claim ran but process died while still 'running'
    import scheduler as S
    orig = S.STALE_SECS
    S.STALE_SECS = -1  # make anything stale
    try:
        sched._claim(job_id)  # now running
        reclaim = sched._reclaim_stale()
        assert reclaim >= 1
    finally:
        S.STALE_SECS = orig
    assert sched.get(job_id)["status"] == "queued"


def test_scheduler_no_double_post_across_publishes(sched):
    job_id, _ = sched.enqueue("facebook_feed", "post C", "acct")
    res1 = sched.publish_due(FacebookPublisher(), {"account_id": "acct"})
    res2 = sched.publish_due(FacebookPublisher(), {"account_id": "acct"})
    done = [r for r in res1 if r["status"] == "done"]
    assert len(done) == 1
    assert res2 == []  # nothing left to publish -> no second post


def test_scheduler_marks_failed_job(sched):
    job_id, _ = sched.enqueue("facebook_feed", "post D", "acct")
    from publisher import HTTPError

    class Boom(FacebookPublisher):
        def send(self, oauth, content):
            raise HTTPError(500)

    sched.publish_due(Boom())
    assert sched.get(job_id)["status"] == "failed"


# ---------------------------------------------------------------------------
# Signature-verified webhooks
# ---------------------------------------------------------------------------
def test_webhook_valid_signature_applies():
    payload = {"job_id": "abc", "status": "delivered"}
    sig = sign("facebook_feed", payload)

    applied = {}
    def handler(platform, body):
        applied.update(body)
        return {"ok": True}

    result = verify_and_apply("facebook_feed", payload, sig, handler)
    assert applied["status"] == "delivered"


def test_webhook_rejects_bad_signature():
    payload = {"job_id": "abc", "status": "delivered"}
    sig = sign("facebook_feed", payload)
    payload["status"] = "HACKED"  # tampered after signing
    with pytest.raises(SignatureError):
        verify_and_apply("facebook_feed", payload, sig, lambda p, b: None)


def test_webhook_rejects_stale_timestamp():
    import time

    from webhooks import sign as s

    payload = {"job_id": "x"}
    sig = s("twitter_card", payload, timestamp=int(time.time()) - 10000)
    with pytest.raises(SignatureError):
        verify_and_apply("twitter_card", payload, sig, lambda p, b: None)


# ---------------------------------------------------------------------------
# Content hash used for idempotency
# ---------------------------------------------------------------------------
def test_content_hash_deterministic():
    assert content_hash("a", ["x"]) == content_hash("a", ["x"])
    assert content_hash("a", ["x"]) != content_hash("a", ["y"])


# ---------------------------------------------------------------------------
# API end-to-end (compose -> schedule -> publish -> signed webhook)
# ---------------------------------------------------------------------------
def test_api_publish_and_signed_webhook(monkeypatch, tmp_path):
    monkeypatch.setenv("SOCIAL_DB", str(tmp_path / "api.db"))
    import main as M

    c = __import__("fastapi.testclient", fromlist=["TestClient"]).TestClient(M.app)
    r = c.post("/posts", json={"platform": "twitter_card", "brand": "Acme",
                               "product": "widget", "hashtags": ["launch"]})
    job_id = r.json()["job_id"]
    assert r.json()["caption"]["chars"] > 0
    pub = c.post("/publish").json()
    assert any(p["status"] == "done" for p in pub["published"])
    sig = sign("twitter_card", {"job_id": job_id, "status": "delivered"})
    wh = c.post("/webhooks/twitter_card", json={"job_id": job_id, "status": "delivered"},
                headers={"x-signature": sig})
    assert wh.json()["status"] == "delivered"
    assert c.get("/posts/" + job_id).json()["status"] == "delivered"
    # bad signature rejected at API boundary
    bad = c.post("/webhooks/twitter_card", json={"job_id": job_id, "status": "HACKED"},
                 headers={"x-signature": "t=1,sha256=deadbeef"})
    assert bad.status_code == 400
