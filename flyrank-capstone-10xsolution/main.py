"""CampaignBooster — 10x solution FastAPI.

Endpoints:
  * POST /campaigns        submit a goal -> run the full pipeline in background
  * GET  /campaigns/{id}   poll stage progress + cost
  * GET  /campaigns/{id}/report  get the markdown/HTML deliverable
  * GET  /health
"""

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from pipeline import Pipeline

pipeline = Pipeline()
app = FastAPI(title="CampaignBooster — 10x Solution", version="1.0.0")


class CampaignRequest(BaseModel):
    goal: str
    provider: str = os.getenv("PLAN_PROVIDER", "mock")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/campaigns")
def create_campaign(body: CampaignRequest):
    if not body.goal or len(body.goal.strip()) < 3:
        raise HTTPException(status_code=422, detail="goal too short")
    run_id = pipeline.submit(body.goal, body.provider)
    return {"campaign_id": run_id, "status": "queued"}


@app.get("/campaigns/{run_id}")
def get_campaign(run_id: str):
    run = pipeline.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="campaign not found")
    return {
        "id": run["id"],
        "status": run["status"],
        "goal": run["goal"],
        "cost_micro_cents": run["cost_micro_cents"],
        "stages": run["ctx"]["stages"],
        "stages_ctx": {k: v for k, v in run["ctx"].items() if k not in ("stages", "goal", "provider")},
        "error": run["error"],
    }


@app.get("/campaigns/{run_id}/report")
def get_report(run_id: str):
    run = pipeline.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="campaign not found")
    if run["status"] != "completed":
        raise HTTPException(status_code=409, detail=f"not ready (status={run['status']})")
    return {"markdown": run["ctx"]["report"]["markdown"],
            "html": run["ctx"]["report"]["html"]}
