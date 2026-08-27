"""Social Media Studio — FastAPI.

Endpoints:
  * POST /posts              compose caption + create image variants + schedule
  * GET  /posts/{id}         job + status
  * POST /publish            run the durable scheduler (publish due jobs)
  * POST /variants/{source}  (optional) create variants from a local file
  * POST /webhooks/{platform}  signature-verified status callbacks
  * GET  /health
"""

import os
import tempfile

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from captions import Caption, compose_for
from publisher import FacebookPublisher, TwitterPublisher
from scheduler import Scheduler
from variants import source_hash
from webhooks import SHARED_SECRETS, verify_and_apply

scheduler = Scheduler()
accounts = {
    "facebook_feed": {"account_id": "page_1"},
    "twitter_card": {"account_id": "handle_1"},
}
PUBLISHERS = {"facebook_feed": FacebookPublisher(), "twitter_card": TwitterPublisher()}

app = FastAPI(title="Social Media Studio", version="1.0.0")


class PostRequest(BaseModel):
    platform: str
    brand: str = "our studio"
    product: str = "a new thing"
    body: str = ""
    cta: str = "Link in bio."
    hook: str = ""
    hashtags: list[str] = Field(default_factory=list)
    account: str = "default"


class VariantRequest(BaseModel):
    platforms: list[str] = Field(default_factory=list)


@app.get("/health")
def health():
    return {"status": "ok", "publishers": list(PUBLISHERS.keys())}


@app.post("/posts")
def create_post(body: PostRequest):
    if body.platform not in PUBLISHERS:
        raise HTTPException(status_code=422, detail=f"unsupported platform: {body.platform}")
    caption: Caption = compose_for(body.model_dump(), body.platform)
    job_id, note = scheduler.enqueue(body.platform, caption.text, body.account)
    return {
        "job_id": job_id,
        "note": note,
        "platform": body.platform,
        "caption": {"text": caption.text, "chars": caption.length},
    }


@app.get("/posts/{job_id}")
def get_post(job_id: str):
    job = scheduler.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.post("/publish")
def publish():
    # publish facebook due jobs (mock transport by default)
    results = []
    for platform in PUBLISHERS:
        results.extend(scheduler.publish_due(PUBLISHERS[platform], accounts[platform]))
    return {"published": results}


@app.get("/variants/specs")
def variant_specs():
    from variants import VARIANT_SPECS

    return VARIANT_SPECS


@app.post("/webhooks/{platform}")
def webhook(platform: str, payload: dict, x_signature: str = Header(default="")):
    if platform not in SHARED_SECRETS:
        raise HTTPException(status_code=404, detail="unknown platform")
    if not x_signature:
        raise HTTPException(status_code=400, detail="missing signature header")

    def handler(plat, body):
        job_id = body.get("job_id")
        status = body.get("status", "delivered")
        if job_id:
            scheduler.mark(job_id, status)
        return {"ok": True, "platform": plat, "job_id": job_id, "status": status}

    try:
        return verify_and_apply(platform, payload, x_signature, handler)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc))
