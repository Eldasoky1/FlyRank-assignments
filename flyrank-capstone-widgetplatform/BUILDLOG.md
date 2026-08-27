# BUILDLOG — Embeddable Widget & Lead-Capture Platform

Honest log of how this was built and where an AI assistant was used.

## Session 1
- Scaffolded project (requirements, .gitignore, .env.example, capstone.yaml).
- Wrote `widget_store.py` (tenants/widgets CRUD + tenant isolation, cached versioned embed bundle, safe side-effect notifier), `abuse.py` (token-bucket rate limiter, honeypot, boundary validation), `geo.py` (A→B provider fallback that degrades to `{}` on failure), `main.py` (FastAPI admin + public routes, CORS).
- Wrote 15 offline tests.
- **AI usage:** assistant drafted skeleton and core logic; I reviewed, then fixed two bugs found by the test run — a module-load ordering bug in `geo.py` (parser referenced before definition) and a monkeypatch target swap in a test. Suite green (15 passed).

## Commands to reproduce
- `venv\Scripts\pip install -r requirements.txt`
- `venv\Scripts\python -m pytest -q`
- `venv\Scripts\python -m uvicorn main:app --port 8001`
