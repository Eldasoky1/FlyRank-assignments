# BE-07 · Connect to an AI API

A single endpoint that asks an LLM for a **judgement** — classifying an
incoming support ticket — and returns a **trustworthy, structured answer**,
never a free-form chatbot reply.

**Task chosen:** classify a support message into a category
(`billing` / `technical` / `account` / `sales` / `other`) with its sentiment,
a confidence score and a tidy 2–6 word subject line.

**Language:** 🐍 Python + FastAPI.

---

## What it does

```
POST /classify   { "message": "I've been charged twice for the same plan" }
  → 200 { "category": "billing", "sentiment": "negative",
          "confidence": 0.94, "tidy_subject": "Double charge on plan",
          "reasoning": "User reports being billed twice for the same plan." }
```

The model is held to a **strict schema**. Every response is parsed as JSON and
validated with Pydantic before it is returned — a malformed answer is retried
(bounded) and finally rejected with `502`.

---

## Free, no-credit-card provider

The client speaks the **OpenAI-compatible API**, so you can point it at any
free provider. [Groq](https://groq.com) (and similar) offer free tiers with a
no-credit-card signup. Configure via `.env`:

```bash
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=your-groq-key
LLM_MODEL=llama-3.3-70b-versatile
```

> Without a key the app uses a deterministic **FakeLLM** so the whole suite
> (including retry and failure paths) runs offline and for free.

---

## The strict schema

`POST /classify` enforces this output contract (`schemas.py`, Pydantic):

```python
class Classification(BaseModel):
    category:  Literal["billing","technical","account","sales","other"]
    sentiment: Literal["positive","neutral","negative"]
    confidence: float           # 0.0 .. 1.0
    tidy_subject: str           # 2 .. 60 chars
    reasoning: str              # 1 .. 300 chars
```

The system prompt instructs the model to return **only** this JSON object. The
endpoint then:
1. extracts the JSON (even from markdown fences),
2. parses it,
3. validates it against `Classification`.

Anything that fails any of those steps is treated as a bad answer.

---

## Timeout & retry logic

Implemented in `llm.py` (`Classifier`):

- **Timeout** — every model call is given a hard timeout
  (`LLM_TIMEOUT`, default **25 s**) via the HTTP client. It fails fast rather
  than hanging the request.
- **Retries (sane stop)** — on a parse error, schema validation error, or a
  transient `ConnectionError`, the call is retried with exponential backoff
  (`backoff * 2**attempt`), up to `LLM_MAX_RETRIES` (default **2**). The loop
  **never retries forever** — it always stops after `max_retries + 1` attempts
  and raises `ClassificationError` → surfaced as `502`.

```
attempt 1 ── bad output ──┐
attempt 2 ────────────────┼─ exponential backoff
attempt 3 ── final ───────┘ -> ClassificationError -> HTTP 502
```

---

## Endpoints

| Method | Path | Body | Success | Errors |
|--------|------|------|---------|--------|
| POST | `/classify` | `{message}` | `200` Classification | `422` bad body, `502` model failed after retries |
| GET | `/` | — | API info | — |
| GET | `/health` | — | `200` `{status: "ok"}` | — |

Swagger UI: `http://localhost:8000/docs`.

---

## Setup & run

```bash
cd BE-07-connect-to-ai-api
python -m venv venv
venv\Scripts\activate            # source venv/bin/activate on Linux/macOS
pip install -r requirements.txt

cp .env.example .env             # add your free-provider key
uvicorn main:app --reload --port 8000
```

Try it with `curl`:

```bash
curl -s -X POST http://localhost:8000/classify \
  -H 'Content-Type: application/json' \
  -d '{"message": "My subscription renewed but I cannot access my reports"}'
```

---

## Running the tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -q
```

**14 tests** — all offline via the fake provider. They prove:

- the HTTP contract (200 / 422),
- strict schema enforcement (invalid category, out-of-range confidence),
- JSON extraction from markdown fences / surrounding text / no-JSON input,
- bounded retries that never run forever (`call_count == retries + 1`),
- retry that succeeds after a bad attempt,
- transient `ConnectionError` (timeout) surfacing as `502` after retries,
- the happy path returning a fully-populated `Classification`.

Environment variables needed: none for tests; only `LLM_API_KEY` etc. for a
real provider.
