"""API-level tests via FastAPI TestClient."""

import pytest
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_meter_requires_idempotency_key():
    r = client.post("/v1/usage", json={"customer_id": "c1", "usage_type": "api_calls", "quantity": 1})
    assert r.status_code == 422


def test_meter_bad_usage_type():
    r = client.post(
        "/v1/usage",
        json={"customer_id": "c1", "usage_type": "nonsense", "quantity": 1},
        headers={"Idempotency-Key": "k1"},
    )
    assert r.status_code == 422


def test_generate_path_works_for_pro():
    main.service.store.upsert_customer("cgen", plan="pro", active=1)
    r = client.post(
        "/generate",
        json={
            "customer_id": "cgen",
            "prompt": "hi",
            "cached_input_tokens": 100,
            "uncached_input_tokens": 200,
            "output_tokens": 50,
            "reasoning_tokens": 10,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["tokens"]["total_tokens"] == 360
    assert data["tokens"]["cost_cents"] >= 0


def test_generate_blocked_on_free_for_ai_tokens():
    main.service.store.upsert_customer("cfree", plan="free", active=1)
    # free plan: api_calls ok (100 limit), but 0 ai_tokens -> 429
    r = client.post(
        "/generate",
        json={"customer_id": "cfree", "prompt": "x", "output_tokens": 10},
    )
    assert r.status_code == 429
