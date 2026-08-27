# BUILDLOG — CampaignBooster (10x Solution)

Honest log of how this was built and where an AI assistant was used.

## Session
- Chose problem (campaign-plan accelerator) and documented the 10x claim.
- Wrote DESIGN.md, MILESTONES.md, SUBMISSION.md, README.md.
- Implemented 6 program concepts: `goal.py` (structured plan), `guardrail.py`
  (reject+explain), `budget.py` (integer-cents cost), `checklist.py`,
  `pipeline.py` (multi-stage orchestration, retries, progress, cost),
  `report.py` (Markdown+HTML deliverable), `main.py` (FastAPI).
- Wrote 12 offline tests.
- **AI usage:** assistant drafted the skeleton and logic; I reviewed and fixed a
  real bug found by tests — the pipeline stage contract was inconsistent: stages
  returned `(output, cost)` tuples while the runner re-wrapped them and returned a
  `None` cost, crashing the cost accumulator (`int += None`). I refactored so each
  stage exposes a `cost_micro_cents` attribute and `run` returns only the output,
  and re-ran tests to green. Verified the full API deliverable end-to-end.

## Commands to reproduce
- `venv\Scripts\pip install -r requirements.txt`
- `venv\Scripts\python -m pytest -q`
- `venv\Scripts\python -m uvicorn main:app --port 8004`
- `POST /campaigns {"goal":"launch a referral program"}`
