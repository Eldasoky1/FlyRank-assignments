# Embeddable Widget & Lead-Capture Platform

FlyRank Capstone — create an embeddable lead-capture widget your customers drop into any site, protected against spam/abuse, and get an owner dashboard.

## What it does
- **Widget management API** (api-key auth) with **tenant isolation** — every query is scoped to the owning tenant.
- **Embed snippet generation** and **cached, versioned delivery** (`/w/{id}.js`) — bumping a widget invalidates the cache and changes the ETag/content version.
- **Public submission endpoint** with CORS, boundary validation (bad input → clean 4xx), honeypot, and **per-IP + per-widget rate limiting → 429**.
- **Geo enrichment with A→B fallback** (ip-api.com → ipapi.co); on failure it **degrades, never fails** (empty geo stored).
- **Safe side effects** — email/webhook failure is swallowed and never blocks lead capture.
- **Owner dashboard stats API** (leads per widget, honeypot/rejection counts).

## Stack
FastAPI · Pydantic · SQLite (stdlib, schema + indexes in code) · in-process token-bucket rate limiter · CORS middleware.

## Run
```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt     # Windows
venv\Scripts\python -m uvicorn main:app --reload --port 8001
```
Seed a demo tenant+widget: `venv\Scripts\python -c "import main; t=main.store.create_tenant('Demo'); w=main.store.create_widget(t['id'],'Newsletter'); print(t['id'], w['id'])"`
Tests (offline): `venv\Scripts\python -m pytest -q`

Requires `X-Api-Key` (default `dev-master-key`, set `MASTER_API_KEY` in `.env`).

## Endpoints
| Method | Path | Purpose |
|---|---|---|
| POST | `/admin/tenants` | create tenant (returns api_key once) |
| POST | `/admin/tenants/{t}/widgets` | create widget |
| GET | `/admin/tenants/{t}/widgets` | list widgets (isolated) |
| PATCH | `/admin/widgets/{id}` | update → bumps version |
| GET | `/admin/tenants/{t}/stats` | dashboard stats |
| GET | `/w/{id}.js` | cached versioned embed |
| POST | `/lead` | public submission |

## Architecture
`main.py` (HTTP/boundary) → `widget_store.py` (store + embed bundle + safe side effects) → `abuse.py` (rate limit/honeypot/validation) → `geo.py` (A→B fallback resolver). Switch `FakeGeoResolver()` → `GeoResolver()` for real providers.

## Limitations
- Geo uses default providers; switch the resolver in `main.py` for production (free tiers rate-limit).
- Tenants/API keys have no rotation/RBAC.
- No hosted test page in this repo (see README of the widget demo), but `/w/{id}.js` is a self-contained embeddable snippet.
