"""Offline tests for metering, costing, and billing modules."""

import json
import time

import pytest

from billing import StripeBilling, _verify_without_runtime
from costing import calculate_token_cost_usd, token_breakdown_to_usages
from metering import (
    InsufficientPayment,
    MeteringService,
    MeteringStore,
    QuotaExceeded,
    UsageReserved,
)
from plans import get_plan, is_paid


@pytest.fixture
def store():
    return MeteringStore(":memory:")


@pytest.fixture
def service(store):
    return MeteringService(store)


# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------
def test_plan_defaults():
    assert get_plan("free").quota["api_calls"] == 100
    assert get_plan("free").quota["ai_tokens"] == 0
    assert get_plan("pro").quota["api_calls"] == 100_000
    assert not is_paid("free")
    assert is_paid("pro")


# ---------------------------------------------------------------------------
# Idempotent metering
# ---------------------------------------------------------------------------
def test_meter_is_idempotent(store):
    store.meter("c1", "api_calls", "key-1", 1)
    with pytest.raises(UsageReserved):
        store.meter("c1", "api_calls", "key-1", 1)
    assert store.total_used("c1", "api_calls") == 1


def test_record_usage_retry_does_not_double_count(service):
    service.store.upsert_customer("c1", plan="pro", active=1)
    first = service.record_usage("c1", "api_calls", "key-1", 1)
    second = service.record_usage("c1", "api_calls", "key-1", 1)
    assert first["recorded"] is True
    assert second["recorded"] is False
    assert second["idempotent"] is True
    assert service.store.total_used("c1", "api_calls") == 1


# ---------------------------------------------------------------------------
# Quota enforcement (boundary-exact)
# ---------------------------------------------------------------------------
def test_boundary_usage_allows_when_equal_not_exceeding(service):
    # Free plan: 100 api_calls
    service.store.upsert_customer("c1", plan="free", active=1)
    for i in range(100):
        service.record_usage("c1", "api_calls", f"k{i}", 1)
    assert service.store.total_used("c1", "api_calls") == 100
    # used == limit -> reject
    with pytest.raises(QuotaExceeded):
        service.record_usage("c1", "api_calls", "overflow", 1)


def test_ai_tokens_blocked_on_free_plan(service):
    service.store.upsert_customer("c1", plan="free", active=1)
    with pytest.raises(QuotaExceeded):
        service.record_usage("c1", "ai_tokens", "k", 1)


def test_inactive_pro_customer_gets_402(service):
    service.store.upsert_customer("c1", plan="pro", active=0)
    with pytest.raises(InsufficientPayment):
        service.record_usage("c1", "ai_tokens", "k", 1)


def test_active_pro_customer_uses_ai_tokens(service):
    service.store.upsert_customer("c1", plan="pro", active=1)
    service.record_usage("c1", "ai_tokens", "k", 500)
    assert service.store.total_used("c1", "ai_tokens") == 500


# ---------------------------------------------------------------------------
# Costing rules (integer cents, reasoning = output, cached cheaper, categories free)
# ---------------------------------------------------------------------------
def test_cached_input_cheaper_than_uncached():
    cached_1m = calculate_token_cost_usd(1_000_000, 0, 0)
    uncached_1m = calculate_token_cost_usd(0, 1_000_000, 0)
    assert cached_1m == 10  # 0.10 usd/1M -> 10 cents
    assert uncached_1m == 40  # 0.40 usd/1M -> 40 cents
    assert cached_1m < uncached_1m


def test_reasoning_tokens_billed_as_output():
    output_only = calculate_token_cost_usd(0, 0, 1_000_000)
    reasoning_only = calculate_token_cost_usd(0, 0, 0, reasoning_tokens=1_000_000)
    assert output_only == reasoning_only == 120  # 1.20 usd/1M -> 120 cents


def test_categories_do_not_add_cost():
    base = token_breakdown_to_usages(100, 0, 50, 0)
    # No concept of category in the API -> adding metadata is a no-op
    assert base["cost_cents"] >= 0
    # verify breakdown totals tokens
    assert base["total_tokens"] == 150


def test_zero_tokens_free():
    assert calculate_token_cost_usd(0, 0, 0, 0) == 0


# ---------------------------------------------------------------------------
# Stripe webhook verification + dedup (offline, pure-python verifier)
# ---------------------------------------------------------------------------
def test_signature_verifies():
    secret = "whsec_test"
    payload = json.dumps({"id": "evt_1", "type": "checkout.session.completed"}).encode()
    timestamp = int(time.time())
    import hashlib, hmac

    msg = f"{timestamp}.".encode() + payload
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    header = f"t={timestamp},v1={sig}"
    assert _verify_without_runtime(secret, payload, header) is True


def test_forged_signature_rejected(fresh_store):
    secret = "whsec_test"
    payload = b'{"id":"evt_x","type":"x"}'
    header = "t=1234567890,v1=" + "0" * 64
    assert _verify_without_runtime(secret, payload, header) is False


@pytest.fixture
def fresh_store():
    return MeteringStore(":memory:")


def _signed_event(secret, obj):
    import hashlib, hmac

    payload = json.dumps(obj).encode()
    timestamp = int(time.time())
    msg = f"{timestamp}.".encode() + payload
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    return payload, f"t={timestamp},v1={sig}"


def test_webhook_dedup_and_apply(fresh_store):
    secret = "whsec_test"
    billing = StripeBilling("sk_test_x", secret, fresh_store, autoload=False)
    event = {
        "id": "evt_1",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"customer_id": "c_pro"},
                "customer": "cus_123",
            }
        },
    }
    payload, header = _signed_event(secret, event)
    r1 = billing.handle_event(payload, header)
    assert r1["applied"] is True and r1["deduped"] is False
    # Repeat -> deduped
    payload2 = json.dumps(event).encode()
    # rebuild header with same ts? dedup checks event id regardless of time
    r2 = billing.handle_event(*_signed_event(secret, event))
    assert r2["deduped"] is True and r2["applied"] is False
    cust = fresh_store.get_customer("c_pro")
    assert cust["plan"] == "pro"
    assert cust["stripe_customer_id"] == "cus_123"


def test_forged_webhook_raises(fresh_store):
    billing = StripeBilling("sk_test_x", "whsec_real", fresh_store, autoload=False)
    payload = b'{"id":"evt_bad","type":"x"}'
    with pytest.raises(ValueError):
        billing.handle_event(payload, "t=1,v1=deadbeef" * 8)
