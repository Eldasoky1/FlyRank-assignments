"""BE-06 · concrete background tasks.

These are the long-running pieces of work executed by the worker pool. Each
receives the manager so it can report progress in stages, and a payload. They
are deliberately slow-ish / staged so the async behaviour is visible.

Registered for the API app in `main.py`.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from job_manager import JobManager

STAGE_DEFS = {
    "normalize": (0, 28, "Normalising records"),
    "enrich": (28, 56, "Enriching with metadata"),
    "score": (56, 82, "Scoring quality"),
    "finalize": (82, 100, "Finalising results"),
}


def process_dataset(manager: "JobManager", job_id: str, payload: dict) -> dict:
    """A staged, long-running data-processing task (the headline demo task).

    Reports progress through four stages. Fails cleanly if the payload says so
    or a required field is missing — so failure handling is testable.
    """
    if payload.get("fail"):
        raise RuntimeError("task requested to fail for testing")

    rows = payload.get("rows", 1000)
    if rows <= 0:
        raise ValueError("rows must be a positive integer")

    total = 0
    for name, (start, end, msg) in STAGE_DEFS.items():
        manager.set_progress(job_id, start, msg)
        time.sleep(payload.get("stage_delay", 0.05))
        # some pretend work over the row range
        acc = 0
        for i in range(rows):
            acc += (i * 7) % 13
        total += acc

    result = {
        "rows_processed": rows,
        "checksum": total,
        "stages_completed": list(STAGE_DEFS.keys()),
    }
    return result


def compile_report(manager: "JobManager", job_id: str, payload: dict) -> dict:
    """Smaller task that assembles a stats blob (ties into BE-08 ideas)."""
    numbers = payload.get("numbers", [10, 20, 30])
    if not isinstance(numbers, list) or not numbers:
        raise ValueError("numbers must be a non-empty list")
    manager.set_progress(job_id, 50, "Computing totals")
    time.sleep(payload.get("stage_delay", 0.02))
    total = sum(numbers)
    return {
        "count": len(numbers),
        "sum": total,
        "average": round(total / len(numbers), 2),
    }


def sleepy(manager: "JobManager", job_id: str, payload: dict) -> dict:
    """Trivial sleep task — mainly for exercise ordering/timing in tests."""
    seconds = float(payload.get("seconds", 0.05))
    time.sleep(seconds)
    manager.set_progress(job_id, 100, "Done")
    return {"slept": seconds}


def build_registry() -> dict:
    return {
        "process_dataset": process_dataset,
        "compile_report": compile_report,
        "sleepy": sleepy,
    }
