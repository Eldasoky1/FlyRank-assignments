# Social Media Studio

FlyRank Capstone — schedule and publish social posts across platforms from one studio: compose platform-sized captions, render image variants, publish through pluggable platform adapters, and track delivery via signature-verified webhooks.

## What it does
- **Caption composer** — copywriting templates (hook / body / CTA / hashtags) with per-platform character limits (truncated gracefully).
- **Image variants** — renders each platform's required size (1200×630 FB, 1600×900 X card, 1080×1080 IG square, 1080×1920 IG story, 1200×627 LinkedIn, 1280×720 YT thumb) with cover/contain crop, content-addressed for dedup.
- **SocialPublisher + adapters** — a common interface with **2 concrete adapters (Facebook, Twitter/X)**. Publishing is **idempotent** (same content → same external id, no double post).
- **429 / Retry-After backoff** — honors the server's retry-after delay and bounded retries before failing.
- **Encrypted OAuth token store** — Fernet-authenticated encryption at rest (PBKDF2-derived key); no plaintext tokens.
- **Durable scheduler** — SQLite-backed queue with **atomic job claims** and **crash recovery** (stale `running` jobs are reclaimed on restart), so a crash never double-posts.
- **Signature-verified webhooks** — HMAC-SHA256 per platform (with timestamp anti-replay) updates a post's status to delivered/errored.

## Stack
FastAPI · Pydantic · Python stdlib (sqlite3, threading, hmac, hashlib) · cryptography (Fernet) · Pillow (image variants) · offline mock transports by default.

## Run
```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt     # Windows
venv\Scripts\python -m uvicorn main:app --reload --port 8003
```
Tests (offline, mock transports): `venv\Scripts\python -m pytest -q`

## Endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness + publishers |
| POST | `/posts` | compose caption + schedule a publish |
| GET | `/posts/{id}` | job + status |
| POST | `/publish` | run the durable scheduler (publish due jobs) |
| GET | `/variants/specs` | platform image size specs |
| POST | `/webhooks/{platform}` | signature-verified status callback (`x-signature`) |

## Idempotent, crash-safe publish
A post is identified by `(platform, content_hash)`. The scheduler claims jobs with a single atomic `UPDATE ... WHERE status='queued'`; if the process dies mid-publish the row stays `running` and is reclaimed after `STALE_SECS`. Combined with the publisher's content-hash idempotency, the same post is never delivered twice even after a crash.

## Measured result
Full offline suite: **20 passed**. API proof: compose → publish (`done` + external id) → signed webhook flips status to `delivered`; tampered/expired signatures are rejected with 400.

## Limitations
- Adapters use offline mock transports; swap in real HTTP to live platforms (same `send` contract).
- Image variant rendering requires a real source image (Pillow).
- Encryption key is dev-default unless `OAUTH_SECRET` is set — set a real secret in production.
