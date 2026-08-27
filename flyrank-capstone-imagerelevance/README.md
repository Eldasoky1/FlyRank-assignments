# AI Image Understanding & Content Matching Engine

FlyRank Capstone — describe images with a vision model as **schema-validated structured output**, rank corpus matches by similarity, and **guard against wrong matches** (e.g. wolf vs fox) instead of guessing.

## What it does
- **Vision structured output** — every describe() call returns a `VisionResult` validated by Pydantic; low-confidence results are **flagged, not guessed** (`low_confidence=True`).
- **Semantic embeddings + similarity ranking** — deterministic hashed bag-of-tokens embeddings + cosine ranking over a 50-image corpus across 5 categories (fox / wolf / dog / bear / deer).
- **Mismatch guard** — rejects a match with an explanation when confidence is low, the predicted category is confusable with the top candidate (wolf vs fox), or is below threshold. Rejections are counted, not forced through.
- **Background batch jobs** — off the request path, with bounded retries + backoff, live progress, and **per-call cost tracking**.
- **Review API** — approve / reject / inspect *why* a match was (or wasn't) accepted.
- **Labeled eval set** — measures **top-1 precision** over 25 labeled images; run the eval and paste the number into EVIDENCE.
- **Vision providers** — `mock` (offline, $0 default), `gemini` (Flash free tier), `ollama` (local, free). Switch via `VISION_PROVIDER`.

## Stack
FastAPI · Pydantic (strict structured output) · Python stdlib (worker threads, hashing embeddings, SQLite in jobs) · no paid API needed in mock mode.

## Run
```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt     # Windows
venv\Scripts\python -m uvicorn main:app --reload --port 8002
```
Seed corpus metadata: `venv\Scripts\python -c "from corpus_data import dump_corpus; print(dump_corpus())"`
Tests (offline): `venv\Scripts\python -m pytest -q`
Eval (top-1 precision): `POST /eval`

## Endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness |
| GET | `/images` | list 50-image corpus |
| POST | `/jobs` | submit background batch job |
| GET | `/jobs/{id}` | poll progress + cost |
| POST | `/eval` | run labeled eval -> top-1 precision |
| GET | `/review/{image_id}` | inspect why |
| POST | `/review/{image_id}/decision` | approve / reject |

## Architecture
`main.py` (HTTP) → `jobs.py` (background runner) → `matcher.py` (embeddings + guard) → `vision.py` (provider adapters + schema) → `corpus_data.py` / `eval.py` / `reviews.py`.

## Measured result (mock provider)
Eval: 25 labeled images → **24 accepted, 1 guarded-rejected** → **top-1 precision 1.0**. The rejection reason (`category mismatch: vision=deer, corpus=bear`) demonstrates the mismatch guard avoiding a wrong match.

## Limitations
- Embeddings are a lightweight bag-of-tokens hash, not a learned model (swap in CLIP via Ollama for a real embedding model).
- Images referenced by free URLs; the engine runs offline on metadata (add real blobs for full offline vision).
- Gemini/Ollama providers need the respective local key/service to run live.
