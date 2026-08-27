"""BE-06 · Background Job API.

Submit long-running work without blocking the request, then poll for
status/progress/result.

    POST /jobs              { "task": "...", "payload": {...} }  -> 202 {job_id}
    GET  /jobs/{id}         -> job status + progress (+ result/error when done)
    GET  /jobs              -> list of jobs
    POST /jobs/{id}/cancel  -> 202 (best-effort, only pre-start jobs)
"""

from fastapi import FastAPI, HTTPException

from job_manager import JobManager
from tasks import build_registry

app = FastAPI(
    title="Background Job API",
    description="Async job queue + worker pool with pollable status.",
    version="1.0.0",
)

manager = JobManager(tasks=build_registry(), worker_count=3)


@app.get("/")
def root():
    return {"name": "Background Job API", "submit": "POST /jobs", "poll": "GET /jobs/{id}"}


@app.post("/jobs", status_code=202)
def submit(payload: dict):
    task = payload.get("task")
    if not task:
        raise HTTPException(status_code=422, detail="'task' is required")
    if task not in manager.tasks:
        raise HTTPException(status_code=422, detail=f"unknown task: {task}")
    data = payload.get("payload") or {}
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="'payload' must be an object")
    job_id = manager.submit(task, data)
    return {"job_id": job_id, "status": "queued"}


@app.get("/jobs")
def list_jobs():
    return {"jobs": [j.to_dict() for j in manager.list()]}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"job {job_id} not found")
    return job.to_dict()


@app.post("/jobs/{job_id}/cancel", status_code=202)
def cancel_job(job_id: str):
    if manager.get(job_id) is None:
        raise HTTPException(status_code=404, detail=f"job {job_id} not found")
    cancelled = manager.cancel(job_id)
    return {"job_id": job_id, "cancelled": cancelled}
