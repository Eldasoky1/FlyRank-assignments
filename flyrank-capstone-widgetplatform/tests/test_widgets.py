"""Tests for the Widget & Lead-Capture platform."""

import time

import pytest
from fastapi.testclient import TestClient

from abuse import RateLimiter, is_honeypot_filled, validate_lead
from geo import FakeGeoResolver, GeoResolver
from widget_store import SafeSideEffects, WidgetStore

import main as app_main

client = TestClient(app_main.app)
MASTER = app_main.MASTER_API_KEY
store = app_main.store


def _admin_tenant(name="Acme"):
    r = client.post(
        "/admin/tenants",
        json={"name": name},
        headers={"X-Api-Key": MASTER},
    )
    assert r.status_code == 200, r.text
    return r.json()["tenant_id"]


def _create_widget(tenant, name="LeadForm"):
    r = client.post(
        f"/admin/tenants/{tenant}/widgets",
        json={"name": name, "title": "Join", "button_label": "Go"},
        headers={"X-Api-Key": MASTER},
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


# ---------------------------------------------------------------------------
# Admin auth + tenant isolation
# ---------------------------------------------------------------------------
def test_admin_requires_key():
    r = client.post("/admin/tenants", json={"name": "X"})
    assert r.status_code == 401


def test_widget_tenant_isolation():
    t1 = _admin_tenant("One")
    t2 = _admin_tenant("Two")
    w1 = _create_widget(t1)
    assert store.get_widget(w1, t2) is None  # not visible to other tenant
    assert store.get_widget(w1, t1) is not None


def test_update_bumps_version_and_invalidates_cache():
    t = _admin_tenant()
    w = _create_widget(t)
    v1 = client.get(f"/w/{w}.js").headers["X-Content-Version"]
    client.patch(
        f"/admin/widgets/{w}",
        json={"title": "New Title"},
        headers={"X-Api-Key": MASTER},
    )
    v2 = client.get(f"/w/{w}.js").headers["X-Content-Version"]
    assert v2 != v1
    body = client.get(f"/w/{w}.js").content
    assert b"New Title" in body


def test_widget_js_cached_and_404_for_missing():
    assert client.get("/w/nonexistent.js").status_code == 404
    t = _admin_tenant()
    w = _create_widget(t)
    r = client.get(f"/w/{w}.js")
    assert r.status_code == 200
    assert "Cache-Control" in r.headers
    assert "ETag" in r.headers


# ---------------------------------------------------------------------------
# Public submission: validation, honeypot, rate limit
# ---------------------------------------------------------------------------
def test_submit_requires_widget():
    assert client.post("/lead", data={"email": "a@b.co"}).status_code == 422


def test_submission_valid_and_geo_enriched():
    t = _admin_tenant()
    w = _create_widget(t)
    r = client.post(
        "/lead",
        data={"widget_id": w, "email": "someone@example.com", "name": "Sally"},
        headers={"X-Forwarded-For": "1.2.3.4"},
    )
    assert r.status_code == 200
    lid = r.json()["lead_id"]
    with store.tx() as c:
        lead = c.execute("SELECT * FROM leads WHERE id=?", (lid,)).fetchone()
    assert lead["email"] == "someone@example.com"
    assert '"country_code": "EG"' in lead["geo"]


def test_invalid_email_rejected():
    t = _admin_tenant()
    w = _create_widget(t)
    r = client.post("/lead", data={"widget_id": w, "email": "not-an-email"})
    assert r.status_code == 422


def test_honeypot_blocked_silently_success():
    t = _admin_tenant()
    w = _create_widget(t)
    r = client.post(
        "/lead",
        data={"widget_id": w, "email": "bot@spam.com", "homepage": "http://spam"},
    )
    # returns fake success but stores nothing as a lead for this email
    assert r.status_code == 200
    with store.tx() as c:
        n = c.execute(
            "SELECT COUNT(*) AS n FROM leads WHERE email=? AND widget_id=?",
            ("bot@spam.com", w),
        ).fetchone()["n"]
    assert n == 0


def test_rate_limit_429():
    t = _admin_tenant()
    w = _create_widget(t)
    app_main.ip_limiter = RateLimiter(rate_per_min=1, burst=1)
    app_main.widget_limiter = RateLimiter(rate_per_min=1, burst=1)
    first = client.post("/lead", data={"widget_id": w, "email": "a@b.co"})
    assert first.status_code == 200
    second = client.post("/lead", data={"widget_id": w, "email": "a@b.co"})
    assert second.status_code == 429


# ---------------------------------------------------------------------------
# Abuse helpers
# ---------------------------------------------------------------------------
def test_honeypot_detection():
    assert is_honeypot_filled({"homepage": "x"}) is True
    assert is_honeypot_filled({"homepage": ""}) is False
    assert is_honeypot_filled({}) is False
    assert is_honeypot_filled({"homepage": ["x"]}) is True


def test_validate_lead():
    assert validate_lead({"email": "user@example.com"}) == (True, "ok")
    ok, _ = validate_lead({"email": ""})
    assert ok is False
    ok, _ = validate_lead({"email": "nope"})
    assert ok is False


def test_rate_limiter_tokens():
    rl = RateLimiter(rate_per_min=10, burst=2)
    assert rl.allow("k") is True
    assert rl.allow("k") is True
    assert rl.allow("k") is False


# ---------------------------------------------------------------------------
# Geo A->B fallback
# ---------------------------------------------------------------------------
def test_geo_fallback_degrades_not_fails(monkeypatch):
    class Boom:
        def __init__(self, *a, **k):
            raise RuntimeError("no network")

    monkeypatch.setattr("geo.httpx.get", Boom)
    resolver = GeoResolver(timeout=0.01)
    # Both providers fail -> returns {} (never raises)
    assert resolver.resolve("8.8.8.8") == {}


def test_fake_geo_resolver():
    r = FakeGeoResolver().resolve("127.0.0.1")
    assert r["country_code"] == "LOCAL"


# ---------------------------------------------------------------------------
# Safe side effects
# ---------------------------------------------------------------------------
def test_side_effects_never_raise(monkeypatch):
    se = SafeSideEffects()
    import httpx

    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(httpx, "post", boom)
    result = se.notify({"email": "a@b.co"}, endpoint="http://example/hook")
    assert result["ok"] is False  # surfaced but does not raise
