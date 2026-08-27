# BUILDLOG — AI Image Understanding & Content Matching Engine

Honest log of how this was built and where an AI assistant was used.

## Session 1
- Scaffolded project (requirements, .gitignore, .env.example, capstone.yaml, corpus metadata).
- Wrote `corpus_data.py` (50 images / 5 categories), `vision.py` (schema-validated adapters for mock/gemini/ollama), `matcher.py` (embeddings + similarity + mismatch guard), `jobs.py` (background runner with retries, progress, cost), `eval.py`, `reviews.py`, `main.py` (FastAPI).
- Wrote 17 offline tests.
- **AI usage:** assistant drafted the skeleton and logic; I reviewed, and fixed a real bug found by tests — job error results weren't persisted (only match+cost), so `completed_with_errors` was never set; fixed `add_result` to carry errors. Also dropped a leftover no-op test. Measured top-1 precision (1.0) and captured guard-rejection proof for EVIDENCE.

## Commands to reproduce
- `venv\Scripts\pip install -r requirements.txt`
- `venv\Scripts\python -m pytest -q`
- `venv\Scripts\python -m uvicorn main:app --port 8002`
- `POST /eval` -> top-1 precision
