# Usage Metering & Billing Engine

FlyRank Capstone — a usage metering and Stripe billing engine.

## What it does
- **Idempotent usage metering** — a client `Idempotency-Key` guarantees retries record exactly one event (never double-counted).
- **Quota enforcement** — boundary-exact: `used == limit` rejects the next event. Returns `429 Too Many Requests` when quota is exhausted and billable; `402 Payment Required` when the account can't consume a paid usage type (no active subscription).
- **AI-token cost rules** — cached input priced cheaper than uncached input; reasoning tokens billed at the output rate; categories/metadata never add cost. Money kept in **integer cents**.
- **Stripe (test mode only)** — Checkout session creation + webhooks (`checkout.session.completed`, `customer.subscription.*`) with signature verification (forged → 400) and event dedup.

## Stack
FastAPI · Pydantic (boundary validation) · SQLite (stdlib, schema+index migrations in code) · `stripe` test-mode client (with a pure-python signature verifier fallback for offline use).

## Run
```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt     # Windows
venv\Scripts\python -m uvicorn main:app --reload --port 8000
```
Seed demo customer: `venv\Scripts\python seed.py`
Tests (offline, no network/keys): `venv\Scripts\python -m pytest -q`

Configure Stripe test keys + webhook secret via `.env` (see `.env.example`). Never commit real keys.

## Endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness |
| POST | `/v1/usage` | meter (requires `Idempotency-Key`) |
| GET | `/v1/usage?customer_id=` | usage summary |
| POST | `/generate` | dummy billable endpoint (API call + tokens) |
| GET | `/checkout?customer_id=` | create Stripe Checkout session (test mode) |
| POST | `/webhooks/stripe` | signature-verified, deduped webhook |

## Architecture
Layered: `main.py` (HTTP/boundary) → `metering.py` (service + store) → `plans.py`/`costing.py` (domain rules), `billing.py` (Stripe adapter). Data in SQLite with uniqueness constraints for idempotency and a `stripe_events` idempotency table.

## Limitations
- Stripe Checkout/webhooks require real **test-mode** keys and the Stripe CLI (`stripe listen`, `stripe trigger`) to exercise fully; offline tests use the pure-python verifier.
- Billing periods roll monthly (`YYYY-MM`); no mid-month proration.
- No multi-tenant UI/dashboard — API + CLI only.
