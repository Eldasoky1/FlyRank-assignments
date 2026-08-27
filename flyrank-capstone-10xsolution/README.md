# CampaignBooster — AI Campaign Plan Accelerator (10x Solution)

The **10x Solution** capstone. One-line campaign goal → a complete, schema-validated
campaign package (plan, guardrail, budget, asset checklist, shareable report) in < 2 seconds.

## What it does
Runs a fixed, visible pipeline over your goal:
1. **Plan** — goal → `CampaignPlan` (channels, audiences, objectives), Pydantic-validated
   output via a pluggable generator (mock offline; LLM provider swappable).
2. **Guardrail** — validates the plan; rejects a vague/incomplete plan with reasons instead
   of silently passing.
3. **Budget** — per-channel cost model → projection in integer cents + USD.
4. **Checklist** — plan → actionable asset checklist with ownership + status.
5. **Report** — composes everything into a Markdown + HTML deliverable.

Everything runs off the request path with retries+backoff, progress, and accumulated cost.

## Program concepts (≥5)
1. Multi-stage pipeline orchestration (background, retries, progress, cost)
2. Structured schema-validated output (Pydantic `CampaignPlan`)
3. Guardrail with rejection + explanation (never a silent wrong pass)
4. Cost & budget accounting (integer-cents model)
5. Report / artifact generation (Markdown + HTML deliverable)
6. Provider abstraction / pluggability (mock default, LLM provider via env)

## Stack
FastAPI · Pydantic · Python stdlib (threading, retries) · no paid API in mock mode.

## Run
```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt     # Windows
venv\Scripts\python -m uvicorn main:app --reload --port 8004
```
Tests (offline): `venv\Scripts\python -m pytest -q`

## Endpoints
| Method | Path | Purpose |
|---|---|---|
| POST | `/campaigns` | submit a goal → run the pipeline (background) |
| GET | `/campaigns/{id}` | poll stage progress + cost |
| GET | `/campaigns/{id}/report` | get the Markdown/HTML deliverable |
| GET | `/health` | liveness |

## Measured result
Full offline suite: **12 passed**. API proof: `launch a referral program for agencies`
→ 5 stages, cost 12 micro-cents, budget $49.50, 15-item ownership checklist, Markdown report.

## Docs
- `DESIGN.md` — one-page design doc
- `MILESTONES.md` — 5 milestones (all delivered)
- `SUBMISSION.md` — "My 10x Solution - El-Dasoky"
