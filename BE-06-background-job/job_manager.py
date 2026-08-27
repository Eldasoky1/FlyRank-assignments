"""BE-06 · Background job system (core).

A tiny job queue + worker pool. Submitting a job returns immediately with a
job id; the actual work runs on background daemon threads, so the request
handlers never block. Callers poll `get()` for status/progress/result.

Status lifecycle:

    queued -> running -> succeeded
                      \-> failed
"""

from __future__ import annotations

import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

TaskFn = Callable[["JobManager", str, dict], dict]


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class Job:
    id: str
    task: str
    payload: dict
    status: JobStatus = JobStatus.QUEUED
    progress: int = 0
    message: str = ""
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task": self.task,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


class JobManager:
    """Queue + worker pool. Thread-safe."""

    def __init__(self, tasks: Dict[str, TaskFn], worker_count: int = 3):
        self.tasks = tasks
        self._worker_count = worker_count
        self._jobs: Dict[str, Job] = {}
        self._queue: "queue.Queue[str]" = queue.Queue()
        self._lock = threading.Lock()
        self._workers: List[threading.Thread] = []
        self._started = False

    # ------------------------------------------------------------- lifecycle

    def _ensure_workers(self):
        if self._started:
            return
        self._started = True
        for _ in range(self._worker_count):
            t = threading.Thread(target=self._worker_loop, daemon=True)
            t.start()
            self._workers.append(t)

    def _worker_loop(self):
        while True:
            job_id = self._queue.get()
            self._dispatch(job_id)

    def _dispatch(self, job_id: str):
        with self._lock:
            job = self._jobs[job_id]
        fn = self.tasks.get(job.task)
        now = time.time()
        with self._lock:
            job.status = JobStatus.RUNNING
            job.started_at = now
        if fn is None:
            self._finish(job_id, status=JobStatus.FAILED, error=f"unknown task: {job.task}")
            return
        try:
            result = fn(self, job_id, job.payload)
            self._finish(job_id, status=JobStatus.SUCCEEDED, progress=100, result=result)
        except Exception as exc:  # noqa: BLE001 - a job failure is data, not a crash
            self._finish(job_id, status=JobStatus.FAILED, error=str(exc))

    def _finish(self, job_id: str, status: JobStatus, **fields):
        with self._lock:
            job = self._jobs[job_id]
            job.status = status
            job.finished_at = time.time()
            for k, v in fields.items():
                setattr(job, k, v)

    # ------------------------------------------------------------- public API

    def submit(self, task: str, payload: Optional[dict] = None) -> str:
        job = Job(id=uuid.uuid4().hex[:12], task=task, payload=payload or {})
        with self._lock:
            self._jobs[job.id] = job
        self._ensure_workers()
        self._queue.put(job.id)
        return job.id

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self) -> List[Job]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda j: j.created_at)

    def cancel(self, job_id: str) -> bool:
        """Best-effort cancel: only applies to jobs not yet processed."""
        removed = False
        with self._lock:
            job = self._jobs.get(job_id)
            if job and job.status == JobStatus.QUEUED:
                job.status = JobStatus.FAILED
                job.error = "cancelled before start"
                job.finished_at = time.time()
                removed = True
        return removed

    def set_progress(self, job_id: str, progress: int, message: str = ""):
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.progress = max(0, min(100, int(progress)))
                job.message = message
