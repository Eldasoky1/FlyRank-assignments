"""BE-06 · tests for the background job system.

Runs 100% offline. Covers: the async submit-then-poll lifecycle, success and
failure, progress reporting, cancellation of a queued job, task validation,
404s, listing, and distinct ids.

Run:
    pip install -r requirements.txt
    pytest tests/ -q
"""

import time

import pytest
from fastapi.testclient import TestClient

from job_manager import JobManager, JobStatus
from tasks import build_registry, process_dataset
import main as main_module


@pytest.fixture(scope="module")
def client():
    return TestClient(main_module.app)


def _wait(client, job_id, timeout=8.0):
    """Poll the API until the job reaches a terminal state."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = client.get(f"/jobs/{job_id}").json()
        if state["status"] in ("succeeded", "failed"):
            return state
        time.sleep(0.03)
    raise AssertionError(f"job {job_id} did not finish in time")


# ---- integration (async submit -> poll) ----


def test_submit_returns_job_id_and_polls_to_success(client):
    r = client.post("/jobs", json={"task": "process_dataset", "payload": {"rows": 500}})
    assert r.status_code == 202
    job_id = r.json()["job_id"]
    state = _wait(client, job_id)
    assert state["status"] == "succeeded"
    assert state["progress"] == 100
    assert state["result"]["rows_processed"] == 500
    assert len(state["result"]["stages_completed"]) == 4


def test_failed_job_reports_error(client):
    r = client.post("/jobs", json={"task": "process_dataset", "payload": {"rows": 100, "fail": True}})
    job_id = r.json()["job_id"]
    state = _wait(client, job_id)
    assert state["status"] == "failed"
    assert state["error"]
    assert state["result"] is None


def test_compile_report_task(client):
    r = client.post("/jobs", json={"task": "compile_report", "payload": {"numbers": [1, 2, 3, 4]}})
    job_id = r.json()["job_id"]
    state = _wait(client, job_id)
    assert state["status"] == "succeeded"
    assert state["result"]["average"] == 2.5


def test_progress_is_reported_mid_run() -> None:
    # a busy task with several stages must expose running + partial progress
    mgr = JobManager(build_registry(), worker_count=1)
    seen = []
    job_id = mgr.submit("process_dataset", {"rows": 2000, "stage_delay": 0.15})
    deadline = time.time() + 4
    while time.time() < deadline:
        job = mgr.get(job_id)
        if job.status in (JobStatus.RUNNING, JobStatus.SUCCEEDED):
            seen.append(job.progress)
        if job.status == JobStatus.SUCCEEDED:
            break
        time.sleep(0.02)
    assert any(0 < p < 100 for p in seen), f"expected partial progress, saw {seen}"


def test_list_jobs_contains_submitted(client):
    client.post("/jobs", json={"task": "compile_report", "payload": {"numbers": [1, 2]}})
    jobs = client.get("/jobs").json()["jobs"]
    assert isinstance(jobs, list)
    assert len(jobs) >= 1


def test_get_unknown_job_404(client):
    assert client.get("/jobs/does-not-exist").status_code == 404


# ---- validation ----


def test_missing_task_422(client):
    r = client.post("/jobs", json={"payload": {}})
    assert r.status_code == 422


def test_unknown_task_422(client):
    r = client.post("/jobs", json={"task": "nope", "payload": {}})
    assert r.status_code == 422


# ---- direct manager unit tests (deterministic) ----


def test_queued_job_can_be_cancelled_before_start():
    mgr = JobManager(build_registry(), worker_count=0)  # no workers -> stays queued
    job_id = mgr.submit("process_dataset", {"rows": 100})
    assert mgr.get(job_id).status == JobStatus.QUEUED
    assert mgr.cancel(job_id) is True
    assert mgr.get(job_id).status == JobStatus.FAILED
    assert "cancelled" in (mgr.get(job_id).error or "")


def test_distinct_ids_and_multiple_jobs():
    mgr = JobManager(build_registry(), worker_count=2)
    a = mgr.submit("compile_report", {"numbers": [1, 2, 3]})
    b = mgr.submit("compile_report", {"numbers": [4, 5]})
    assert a != b
    deadline = time.time() + 6
    while time.time() < deadline:
        if mgr.get(a).status == JobStatus.SUCCEEDED and mgr.get(b).status == JobStatus.SUCCEEDED:
            break
        time.sleep(0.03)
    assert mgr.get(a).status == JobStatus.SUCCEEDED
    assert mgr.get(b).status == JobStatus.SUCCEEDED


def test_task_function_directly():
    # process_dataset honors progress through stages and returns a result
    mgr = JobManager(build_registry(), worker_count=0)
    job_id = mgr.submit("process_dataset", {"rows": 10})
    result = process_dataset(mgr, job_id, {"rows": 10})
    assert result["rows_processed"] == 10
    assert result["checksum"] >= 0
