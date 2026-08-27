# BUILDLOG — Usage Metering & Billing Engine

Honest log of how this was built and where an AI assistant was used.

## Session 1
- Scaffolded project (requirements, .gitignore, .env.example, capstone.yaml).
- Wrote domain modules: `plans.py`, `costing.py`, `metering.py` (SQLite store, idempotency, quota, 429/402), `billing.py` (Stripe test-mode adapter + pure-python verifier), `main.py` (FastAPI), `seed.py`.
- Wrote offline tests (20) covering idempotency, boundary-exact quota, cost rules, webhook signature verify + dedup.
- **AI usage:** assistant drafted the skeleton and core logic, I reviewed each module, fixed a signature-verifier bug (bad header split) found by a failing test, and verified the suite (20 passed).

## Commands to reproduce
- `venv\Scripts\pip install -r requirements.txt`
- `venv\Scripts\python -m pytest -q`
- `venv\Scripts\python seed.py`
- `venv\Scripts\python -m uvicorn main:app --port 8000`

## What a stranger needs
- Stripe test keys + webhook secret in `.env` for the live Stripe pieces; the offline test suite needs nothing.
