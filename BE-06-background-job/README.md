# BE-06 · Background Job

A minimal-but-real **async job system**: long-running work is submitted and
runs on a background **worker pool**, so HTTP requests never block. Callers
poll a job id for status, progress and result.

**Language:** 🐍 Python (threading-based queue + worker pool) + FastAPI.

---

## The problem

Some operations are too slow to run inside a request: heavy data processing,
report generation, model inference. Blocking the request is bad UX and wastes
worker time. The classic answer is a **job queue + workers**:

1. `POST /jobs` accepts work and **returns immediately** with a `job_id`
   (HTTP 202).
2. Background **workers** pull the job from the queue and run it.
3. The caller **polls** `GET /jobs/{id}` to watch status/progress and collect
   the result when done.

That async submit-then-poll pattern is exactly what we build here.

```
Client                      API                      Worker pool
  |  POST /jobs                |                          |
  |--------------------------->| 202 {job_id}             |
  |  (request returns fast)    |------> queued            |
  |                            |       +------> running   |
  |  GET /jobs/{id} (poll)     |       |   progress 0→100 |
  |--------------------------->|       |                  |
  |<----- succeeded + result   |<------+                  |
```

## Status lifecycle

```
queued ──▶ running ──▶ succeeded
              └────▶ failed        (task raised, or cancelled before start)
```

Each job tracks `status`, `progress` (0–100), `message`, `result`, `error`,
and created/started/finished timestamps.

---

## Files

```
BE-06-background-job/
├── job_manager.py   # Job model + JobManager (queue + daemon worker pool)
├── tasks.py         # the concrete background tasks (registry)
├── main.py          # FastAPI: submit / poll / list / cancel
├── tests/test_jobs.py
└── README.md
```

## Run it

```bash
cd BE-06-background-job
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

uvicorn main:app --port 8000
```

## API

| Method | Path | Body / notes |
|--------|------|--------------|
| POST | `/jobs` | `{"task": "...", "payload": {...}}` → `202 {job_id}` |
| GET | `/jobs/{id}` | poll → status/progress/result/error |
| GET | `/jobs` | list all jobs |
| POST | `/jobs/{id}/cancel` | best-effort cancel (queued jobs only) |

```bash
# submit
curl -s -X POST http://localhost:8000/jobs \
  -H 'Content-Type: application/json' \
  -d '{"task":"process_dataset","payload":{"rows":5000}}'
# -> {"job_id":"ab12cd34ef56","status":"queued"}

# poll
curl -s http://localhost:8000/jobs/ab12cd34ef56
# -> {"id":..., "status":"succeeded","progress":100,"result":{...},...}
```

---

## How it works

- `JobManager` holds a thread-safe `job_id -> Job` map and a `queue.Queue` of
  pending ids.
- `submit()` creates a `Job`, enqueues it, and lazily starts **daemon worker
  threads** (so they never block process shutdown).
- Each worker pulls an id, flips it to `running`, dispatches to the registered
  task, and on success stores the result / on exception stores the error.
- Tasks update progress via `manager.set_progress(id, pct, msg)` under the
  manager lock — so polls always read a consistent snapshot.

The **task registry** (`tasks.py`) is one line per task:

```python
def build_registry():
    return {
        "process_dataset": process_dataset,   # staged, long-running
        "compile_report":  compile_report,
        "sleepy":          sleepy,
    }
```

---

## Tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -q
```

**11 tests**, all offline and deterministic. Coverage:

- submit → poll → **succeeded** with `progress == 100` and the right result,
- a failing task becomes **failed** with an error (no exception escapes),
- the `compile_report` task computes its result correctly,
- **partial progress is reported** while a job is still running,
- `/jobs` lists submitted jobs and unknown ids return **404**,
- missing / unknown task names return **422**,
- a still-queued job can be **cancelled** before a worker picks it up,
- the manager issues distinct ids and completes **multiple jobs concurrently**,
- the `process_dataset` task function is unit-tested directly on its stages.
