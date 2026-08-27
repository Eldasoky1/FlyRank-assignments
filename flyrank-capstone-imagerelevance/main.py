"""AI Image Understanding & Content Matching Engine — FastAPI.

Endpoints:
  * POST /jobs            submit a batch vision+match job (background)
  * GET  /jobs/{id}       poll progress + cost
  * POST /eval            run labeled eval set -> top-1 precision + rejections
  * GET  /review/{image_id}        inspect WHY (match + vision + guard)
  * POST /review/{image_id}/decision  approve / reject
  * GET  /images           list corpus
  * GET  /health
"""

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from corpus_data import CORPUS, by_id, dump_corpus
from eval import EvalSet
from jobs import BatchRunner, JobStore
from matcher import Matcher
from reviews import ReviewStore
from vision import build_adapter

# ---------------------------------------------------------------------------
# Wiring
# ---------------------------------------------------------------------------
dump_corpus()  # persist images.json once

VISION_PROVIDER = os.getenv("VISION_PROVIDER", "mock")
adapter = build_adapter(
    VISION_PROVIDER, CORPUS,
    config={
        "api_key": os.getenv("GEMINI_API_KEY", ""),
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "model": os.getenv("OLLAMA_MODEL", "llava"),
    },
)
matcher = Matcher(CORPUS)
job_store = JobStore()
runner = BatchRunner(job_store, matcher, adapter)
reviews = ReviewStore()

app = FastAPI(title="AI Image Understanding & Content Matching Engine", version="1.0.0")


class SubmitRequest(BaseModel):
    image_ids: list[str] = Field(default_factory=list, max_length=500)


# ---------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "provider": VISION_PROVIDER, "corpus": len(CORPUS)}


@app.get("/images")
def images():
    return {"count": len(CORPUS), "images": CORPUS}


# ---------------------------------------------------------------------------
# Batch jobs (off request path)
# ---------------------------------------------------------------------------
@app.post("/jobs")
def submit_job(body: SubmitRequest):
    ids = body.image_ids or [e["id"] for e in CORPUS]
    # validate ids
    unknown = [i for i in ids if not by_id(i)]
    if unknown:
        raise HTTPException(status_code=422, detail=f"unknown image ids: {unknown[:5]}")
    job_id = runner.submit(ids)
    return {"job_id": job_id, "status": "queued"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    # load results into review store for inspection
    for r in job["results"]:
        if "match" in r and r["match"] and "vision" in r:
            reviews.submit(r["image_id"], r["match"], r["vision"])
    return {
        "id": job["id"],
        "status": job["status"],
        "total": job["total"],
        "processed": job["processed"],
        "retries": job["retries"],
        "cost_micro_cents": job["cost_micro_cents"],
        "error": job["error"],
    }


# ---------------------------------------------------------------------------
# Eval set -> top-1 precision
# ---------------------------------------------------------------------------
@app.post("/eval")
def run_eval():
    es = EvalSet()
    return es.run(matcher, adapter)


# ---------------------------------------------------------------------------
# Review API (approve / reject / inspect why)
# ---------------------------------------------------------------------------
@app.get("/review/{image_id}")
def inspect(image_id: str):
    rec = reviews.explain(image_id)
    if not rec:
        # allow ad-hoc inspection by running the describe+match now
        img = by_id(image_id)
        if not img:
            raise HTTPException(status_code=404, detail="image not found")
        vr = adapter.describe(img)
        m = matcher.match(vr)
        reviews.submit(image_id, m.to_dict() if m else None, {
            "subject": vr.subject, "confidence": vr.confidence,
            "low_confidence": vr.low_confidence, "category": vr.category,
        })
        return reviews.explain(image_id)
    return rec


class DecisionRequest(BaseModel):
    approve: bool
    note: str = ""


@app.post("/review/{image_id}/decision")
def decide(image_id: str, body: DecisionRequest):
    rec = reviews.decision(image_id, body.approve, body.note)
    if not rec:
        raise HTTPException(status_code=404, detail="image not reviewed yet")
    return {"image_id": image_id, "decision": rec["decision"], "note": rec["note"]}
