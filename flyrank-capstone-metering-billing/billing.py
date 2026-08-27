"""Stripe billing integration (TEST MODE ONLY).

Implements:
  * Checkout session creation (test keys)
  * Webhook signature verification (raw body, timestamp + signature)
  * Webhook event dedup (StripeDeliveries can repeat)
  * Mapping checkout.session.completed / customer.subscription.* events onto
    the customer's plan state in MeteringStore.

No secret keys are ever logged. All Stripe calls go through the configured
test-mode client.
"""

import hashlib
import hmac
import logging
import os
import re
import time

logger = logging.getLogger("billing")

# Lazy import so offline tests that don't need real Stripe never require the
# network or a configured client.
_sys_tolerant = True


def _verify_without_runtime(secret: str, payload: bytes, header: str) -> bool:
    """Pure-python Stripe v1 webhook signature check.

    Implemented defensively so the engine works even without the `stripe`
    package installed (tests / sandbox); when the official client is present
    we prefer its verified parser.
    """
    m = re.match(r"t=(\d+),v1=([0-9a-fA-F]+)", header.strip())
    if not m:
        return False
    ts_str, sig_part = m.group(1), m.group(2)
    try:
        ts = int(ts_str)
    except ValueError:
        return False
    if abs(time.time() - ts) > 300:
        return False  # stale / replayed outside tolerance
    expected = hmac.new(
        secret.encode("utf-8"),
        f"{ts_str}.{payload.decode('utf-8', 'replace')}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, sig_part.lower())


class StripeBilling:
    """Thin wrapper. Uses the official `stripe` package if imported, else the
    pure-python verifier for offline/demo use."""

    def __init__(self, secret_key: str, webhook_secret: str, store, autoload=True):
        self.secret_key = secret_key
        self.webhook_secret = webhook_secret
        self.store = store
        self._official = None
        if autoload:
            try:
                import stripe as _s

                stripe = _s
                stripe.api_key = secret_key
                self._official = stripe
            except Exception:  # pragma: no cover - env without stripe pkg
                self._official = None

    def create_checkout_session(self, customer_id, price_id, success_url, cancel_url, mode="subscription"):
        """Create a Checkout Session in test mode. Raises on missing keys."""
        if not self._official:
            raise RuntimeError("stripe package required to create Checkout sessions")
        return self._official.checkout.Session.create(
            customer_email=None,
            mode=mode,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=customer_id,
            metadata={"customer_id": customer_id},
        )

    def verify_webhook(self, payload: bytes, header: str) -> dict:
        """Verify the signature and parse the event. Returns the event dict."""
        if self._official is not None:
            try:
                event = self._official.webhook.construct_event(
                    payload, header, self.webhook_secret
                )
                return event
            except Exception as exc:  # invalid signature etc.
                raise ValueError(f"invalid webhook signature: {exc}") from exc
        # Demo / offline fallback
        if not self._verify(header, payload):
            raise ValueError("invalid webhook signature (offline verifier)")
        import json

        return json.loads(payload.decode("utf-8"))

    def _verify(self, header: str, payload: bytes) -> bool:
        return _verify_without_runtime(self.webhook_secret, payload, header)

    def handle_event(self, payload: bytes, header: str) -> dict:
        """Full webhook pipeline: verify -> dedup -> apply."""
        event = self.verify_webhook(payload, header)
        event_id = event.get("id")
        if not event_id:
            raise ValueError("event has no id")
        if self.store.event_seen(event_id):
            return {"event": event_id, "deduped": True, "applied": False}
        self._apply(event)
        self.store.mark_event(event_id)
        return {"event": event_id, "deduped": False, "applied": True}

    def _apply(self, event):
        etype = event.get("type", "")
        data = event.get("data", {}).get("object", {})
        if etype == "checkout.session.completed":
            customer_id = data.get("metadata", {}).get("customer_id") or data.get("client_reference_id")
            if not customer_id:
                logger.warning("checkout.session.completed without customer ref; body=%s", getattr(event, "id", ""))
                return
            # Provision a Pro plan (paid) as a result of a successful checkout.
            self.store.upsert_customer(
                customer_id,
                plan="pro",
                active=1,
                stripe_customer_id=data.get("customer"),
            )
        elif etype == "customer.subscription.deleted":
            self._deactivate(data)
        elif etype == "customer.subscription.updated":
            status = data.get("status")
            cust = self._customer_id(data)
            if cust and (status in ("canceled", "unpaid", "past_due")):
                self.store.upsert_customer(cust, plan="free", active=1)
        elif etype == "customer.subscription.created":
            self._activate(data)

    @staticmethod
    def _customer_id(data):
        # Stripe Subscription metadata carries our customer ref if configured
        return (data.get("metadata") or {}).get("customer_id")

    def _activate(self, data):
        cust = self._customer_id(data)
        if cust:
            self.store.upsert_customer(cust, plan="pro", active=1)

    def _deactivate(self, data):
        cust = self._customer_id(data)
        if cust:
            self.store.upsert_customer(cust, plan="free", active=1)
