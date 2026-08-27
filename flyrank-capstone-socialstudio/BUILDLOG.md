# BUILDLOG — Social Media Studio

Honest log of how this was built and where an AI assistant was used.

## Session
- Scaffolded project (requirements incl. cryptography + Pillow, .gitignore, .env.example, capstone.yaml).
- Wrote `variants.py` (Pillow cover/contain render, content-addressed), `captions.py` (copywriting templates + per-platform limits), `oauth_store.py` (Fernet-encrypted tokens), `publisher.py` (Facebook + Twitter/X adapters, content-hash idempotency, 429/Retry-After backoff), `scheduler.py` (SQLite durable queue, atomic claims, crash recovery), `webhooks.py` (HMAC verification + anti-replay), `main.py` (FastAPI), and 20 offline tests.
- **AI usage:** assistant drafted the skeleton and logic; I reviewed and fixed several real bugs found by tests:
  - `captions.py` f-string had a nested-quote syntax error (`"today's drop"` inside an f-string) — rewrote the line.
  - SQLite "database is locked" — `_conn()` held a read transaction while a separate connection claimed jobs; switched connections to autocommit (`isolation_level=None`).
  - **Scheduler used the module-global `DB_PATH` instead of `self.db_path`**, so tests silently shared one DB (produced cross-test "already done" results). Threaded `self.db_path` through every connection.
  - Webhook signature header didn't bind — `x_signature` needs FastAPI `Header(alias)`; after that the signed callback correctly set status to `delivered`.
  - Honoured `retry_after` exactly (why the backoff test takes a few seconds).

## Commands to reproduce
- `venv\Scripts\pip install -r requirements.txt`
- `venv\Scripts\python -m pytest -q`
- `venv\Scripts\python -m uvicorn main:app --port 8003`
