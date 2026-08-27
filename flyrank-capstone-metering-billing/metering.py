"""Idempotent usage metering + quota enforcement.

Idempotency: a client-supplied idempotency key guarantees that retries record
the usage exactly once. Quota is checked BEFORE recording so a single logical
event never over-consumes.

Quota semantics (boundary-exact):
  * limit == 0  -> feature blocked for this plan
  * used <  limit  -> allowed
  * used == limit -> next event is rejected
  * used >= limit -> rejected

Error classification:
  * 402 Payment Required  -> usage blocked because the account is not on a
                             paid plan that can actually be used (no active
                             subscription / plan not billable).
  * 429 Too Many Requests -> the account IS billable but has exhausted its
                             quota for the current cycle.
"""

import sqlite3
import time
from contextlib import contextmanager

from plans import USAGE_TYPES, get_plan, is_paid


class InsufficientPayment(Exception):
    """402 - account cannot use this usage type (no active paid plan)."""

    def __init__(self, message="payment required to use this feature"):
        super().__init__(message)

    status_code = 402


class QuotaExceeded(Exception):
    """429 - account billable but over/beyond quota."""

    def __init__(self, usage_type, used, limit, message=None):
        self.usage_type = usage_type
        self.used = used
        self.limit = limit
        super().__init__(
            message
            or f"quota exceeded for {usage_type}: used {used}/{limit}"
        )

    status_code = 429


class UsageReserved(Exception):
    """Idempotent re-delivery: event already recorded. Not an error to caller
    that retried, but signals no double-counting happened."""


SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id            TEXT PRIMARY KEY,
    plan          TEXT NOT NULL,
    active        INTEGER NOT NULL DEFAULT 1,
    stripe_customer_id TEXT
);
CREATE TABLE IF NOT EXISTS usage_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    idempotency_key TEXT NOT NULL,
    customer_id     TEXT NOT NULL,
    usage_type      TEXT NOT NULL,
    quantity        INTEGER NOT NULL,
    cost_cents      INTEGER NOT NULL DEFAULT 0,
    recorded_at     INTEGER NOT NULL,
    UNIQUE(customer_id, idempotency_key, usage_type)
);
CREATE TABLE IF NOT EXISTS usage_totals (
    customer_id TEXT NOT NULL,
    usage_type  TEXT NOT NULL,
    period_ref  TEXT NOT NULL,
    total       INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (customer_id, usage_type, period_ref)
);
CREATE TABLE IF NOT EXISTS stripe_events (
    event_id    TEXT PRIMARY KEY,
    processed   INTEGER NOT NULL DEFAULT 1,
    processed_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_usage_cust_type ON usage_totals(customer_id, usage_type);
"""


class MeteringStore:
    """SQLite-backed store for customers, usage, and dedup."""

    def __init__(self, db_path=":memory:"):
        self._path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self._lock = __import__("threading").RLock()

    @contextmanager
    def tx(self):
        with self._lock:
            yield self.conn
            self.conn.commit()

    # --- customers ---
    def upsert_customer(self, customer_id, plan="free", active=1, stripe_customer_id=None):
        with self.tx() as c:
            c.execute(
                """INSERT INTO customers (id, plan, active, stripe_customer_id)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET plan=excluded.plan,
                     active=excluded.active,
                     stripe_customer_id=excluded.stripe_customer_id""",
                (customer_id, plan, int(active), stripe_customer_id),
            )

    def get_customer(self, customer_id):
        with self.tx() as c:
            row = c.execute(
                "SELECT * FROM customers WHERE id = ?", (customer_id,)
            ).fetchone()
            return dict(row) if row else None

    # --- usage ---
    def meter(self, customer_id, usage_type, idempotency_key, quantity=1, cost_cents=0):
        """Record usage exactly once for (customer, idempotency_key, usage_type).

        Raises UsageReserved if already recorded (idempotent re-delivery).
        """
        if usage_type not in USAGE_TYPES:
            raise ValueError(f"invalid usage type: {usage_type}")
        period_ref = current_period_ref()
        with self.tx() as c:
            prior = c.execute(
                """SELECT id FROM usage_records
                   WHERE customer_id=? AND idempotency_key=? AND usage_type=?
                   LIMIT 1""",
                (customer_id, idempotency_key, usage_type),
            ).fetchone()
            if prior:
                raise UsageReserved("already recorded")
            c.execute(
                """INSERT INTO usage_records
                   (idempotency_key, customer_id, usage_type, quantity, cost_cents, recorded_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (idempotency_key, customer_id, usage_type, quantity, cost_cents, int(time.time())),
            )
            c.execute(
                """INSERT INTO usage_totals (customer_id, usage_type, period_ref, total)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(customer_id, usage_type, period_ref)
                   DO UPDATE SET total = total + excluded.total""",
                (customer_id, usage_type, period_ref, quantity),
            )
            return True

    def total_used(self, customer_id, usage_type, period_ref=None):
        period_ref = period_ref or current_period_ref()
        with self.tx() as c:
            row = c.execute(
                """SELECT total FROM usage_totals
                   WHERE customer_id=? AND usage_type=? AND period_ref=?""",
                (customer_id, usage_type, period_ref),
            ).fetchone()
            return row["total"] if row else 0

    # --- stripe event dedup ---
    def event_seen(self, event_id):
        with self.tx() as c:
            row = c.execute(
                "SELECT 1 FROM stripe_events WHERE event_id=?", (event_id,)
            ).fetchone()
            return row is not None

    def mark_event(self, event_id):
        with self.tx() as c:
            c.execute(
                """INSERT OR IGNORE INTO stripe_events (event_id, processed, processed_at)
                   VALUES (?, 1, ?)""",
                (event_id, int(time.time())),
            )


def current_period_ref(now=None):
    """Monthly period reference YYYY-MM."""
    now = now or time.gmtime()
    return time.strftime("%Y-%m", now)


class MeteringService:
    def __init__(self, store: MeteringStore):
        self.store = store

    def ensure_customer(self, customer_id):
        cust = self.store.get_customer(customer_id)
        if not cust:
            self.store.upsert_customer(customer_id, plan="free", active=1)
            cust = self.store.get_customer(customer_id)
        return cust

    def check_quota(self, customer_id, usage_type):
        """Raise InsufficientPayment (402) or QuotaExceeded (429) as needed.

        Boundary-exact:
          limit 0            -> blocked (feature not in plan). If the plan is a
                                paid-only usage type and the customer is not
                                billable => 402, else 429.
          used >= limit      -> exhausted -> 429 (billable) ... unless plan not
                                active -> 402.
        """
        cust = self.ensure_customer(customer_id)
        plan = get_plan(cust["plan"])
        limit = plan.quota.get(usage_type, 0)
        used = self.store.total_used(customer_id, usage_type)
        billable = bool(cust["active"]) and (not is_paid(cust["plan"]) or cust["active"])
        # A paid plan whose account/label is not set as active means you must
        # pay (Stripe checkout) before using.
        if not billable or (is_paid(cust["plan"]) and not cust["active"]):
            raise InsufficientPayment(
                f"{usage_type} requires an active paid subscription"
            )
        if limit == 0:
            raise QuotaExceeded(usage_type, used, limit)
        if used >= limit:
            raise QuotaExceeded(usage_type, used, limit)
        return {"plan": cust["plan"], "limit": limit, "used": used, "remaining": limit - used}

    def record_usage(self, customer_id, usage_type, idempotency_key, quantity=1, cost_cents=0):
        self.check_quota(customer_id, usage_type)
        try:
            self.store.meter(customer_id, usage_type, idempotency_key, quantity, cost_cents)
        except UsageReserved:
            return {"recorded": False, "idempotent": True}
        return {"recorded": True, "idempotent": False}

    def usage_summary(self, customer_id):
        cust = self.ensure_customer(customer_id)
        plan = get_plan(cust["plan"])
        out = {}
        for ut in USAGE_TYPES:
            used = self.store.total_used(customer_id, ut)
            out[ut] = {"used": used, "limit": plan.quota.get(ut, 0)}
        return {"customer_id": customer_id, "plan": cust["plan"], "usage": out}
