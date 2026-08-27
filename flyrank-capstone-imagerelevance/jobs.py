"""Background batch job engine: retries + progress + per-call cost tracking.

Worker pool processes labeled images off the request path. On failure it
retries (bounded). Progress and per-call cost (micro-cost to avoid float
drift) are tracked. Off the request path via threading; state in a store.
"""

from __future__ import annotations

import concurrent.futures
import threading
import time
import uuid

from matcher import Matcher
from vision import VisionResult


class JobStore:
    def __init__(self):
        self._jobs = {}
        self._lock = threading.Lock()

    def create(self, image_ids):
        job_id = uuid.uuid4().hex[:8]
        with self._lock:
            self._jobs[job_id] = {
                "id": job_id,
                "status": "queued",
                "image_ids": image_ids,
                "total": len(image_ids),
                "processed": 0,
                "retries": 0,
                "max_retries": int(_cfg("MAX_RETRIES", "2")),
                "results": [],
                "cost_micro_cents": 0,
                "error": None,
                "created_at": time.time(),
            }
        return job_id

    def get(self, job_id):
        with self._lock:
            return self._jobs.get(job_id)

    def set_status(self, job_id, status, error=None):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = status
                if error:
                    self._jobs[job_id]["error"] = error

    def add_result(self, job_id, image_id, match, cost_micro_cents, error=None):
        with self._lock:
            j = self._jobs[job_id]
            j["processed"] += 1
            j["cost_micro_cents"] += cost_micro_cents
            r = {"image_id": image_id, "match": match}
            if error:
                r["error"] = error
            j["results"].append(r)


def _cfg(k, default):
    import os

    v = os.getenv(k, default)
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


class BatchRunner:
    def __init__(self, store: JobStore, matcher: Matcher, vision_adapter, workers=4):
        self.store = store
        self.matcher = matcher
        self.vision = vision_adapter
        self.workers = workers

    def submit(self, image_ids):
        job_id = self.store.create(image_ids)
        t = threading.Thread(target=self._run, args=(job_id, image_ids), daemon=True)
        t.start()
        return job_id

    def _run(self, job_id, image_ids):
        self.store.set_status(job_id, "running")
        catalog_lookup = {e["id"]: e for e in self.matcher.catalog}

        def process(image_id):
            img = catalog_lookup.get(image_id)
            if not img:
                return {"image_id": image_id, "error": "unknown image"}
            # retries with backoff
            last_err = None
            for attempt in range(self.store.get(job_id)["max_retries"] + 1):
                try:
                    vr = self.vision.describe(img)
                    if not isinstance(vr, VisionResult):
                        raise TypeError("vision did not return VisionResult")
                    match = self.matcher.match(vr)
                    cost = self.vision.cost_cents() * 100  # cents -> micro-cents
                    return {"image_id": image_id, "match": match.to_dict() if match else None,
                            "vision": {"subject": vr.subject, "confidence": vr.confidence,
                                       "low_confidence": vr.low_confidence, "category": vr.category},
                            "cost_micro_cents": int(cost)}
                except Exception as exc:  # noqa: BLE001
                    last_err = str(exc)
                    time.sleep(0.05 * (attempt + 1))
            return {"image_id": image_id, "error": last_err}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as ex:
            for res in ex.map(process, image_ids, chunksize=1):
                self.store.add_result(
                    job_id, res["image_id"], res.get("match"), res.get("cost_micro_cents", 0),
                    error=res.get("error"),
                )
        # mark failed if any error
        job = self.store.get(job_id)
        if any("error" in r and r.get("error") for r in job["results"]):
            self.store.set_status(job_id, "completed_with_errors")
        else:
            self.store.set_status(job_id, "completed")
