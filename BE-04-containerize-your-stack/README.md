# BE-04 · A3 — Containerize your stack

Run the **Task API** (the A2 service) against a **real Postgres** container,
and start the whole stack (app + database) with **one command**.

The core idea this assignment proves: **switching storage touches exactly
one file**. The HTTP routes and service logic are byte-for-byte identical to
A2 — only the storage backend behind them changes, selected by the
`DATABASE_URL` environment variable.

---

## What it is

| Component | Role |
|-----------|------|
| `app/main.py`       | FastAPI service — **identical routes** to A2 `/tasks` CRUD + `/stats` |
| `app/repository.py` | The **repository layer**: an interface + two implementations |
| `db/init.sql`       | Postgres schema (creates `tasks`, adds an index, seeds 3 rows) |
| `docker-compose.yml`| `db` + `app` together; `docker compose up` runs the whole stack |
| `Dockerfile`        | Builds the app image |

### `app/repository.py` in one picture

```
        ┌─────────────────────────────────────────────┐
        │            TaskRepository (interface)        │
        │   list · get · create · update · delete  ·   │
        │   stats                                      │
        └─────────────────────────────────────────────┘
                          ▲              ▲
              ┌───────────┘              └───────────┐
  ┌────────────┴───────────┐            ┌────────────┴───────────┐
  │  InMemoryTaskRepository │            │  PostgresTaskRepository │
  │  (A2 demo store, dict)  │            │  (real Postgres)        │
  └─────────────────────────┘            └─────────────────────────┘

    repo = repo_from_env()   ← the ONLY place that knows the concrete class
```

- `main.py` never imports Postgres or in-memory code directly.
- `repo_from_env()` looks at `DATABASE_URL` and returns the right backend.
- **To switch storage you touch one module (`repository.py`) and one env var —
  routes and service logic are unchanged.** This is stated honestly so you can
  verify it by diffing `main.py` against the A2 version.

---

## Setup

Prerequisites: [Docker](https://www.docker.com/) (with Compose v2).

```bash
cd BE-04-containerize-your-stack
cp .env.example .env        # connection string comes from here
docker compose up --build
```

> **`docker compose up` starts both services**: the Postgres database (with a
> named volume) and the FastAPI app, wired together via the compose network.

That's the **single start command**. If port `8000` is busy, change
`APP_PORT` in `.env`.

Open the API: <http://localhost:8000/docs> (Swagger UI).

---

## Environment variables

Provided via `.env` (gitignored — never committed). `.env.example` is the
committed template.

| Variable | Default | Purpose |
|----------|---------|---------|
| `POSTGRES_USER` | `taskuser` | DB role (used by compose + app) |
| `POSTGRES_PASSWORD` | `taskpass` | DB password |
| `POSTGRES_DB` | `taskdb` | Database name |
| `POSTGRES_PORT` | `5432` | Host port for Postgres |
| `APP_PORT` | `8000` | Host port for the app |
| `DATABASE_URL` | — | **The connection string** the app uses to reach Postgres |

The `DATABASE_URL` in `.env` points at the compose service name (`db`), so it
resolves inside the Docker network.

---

## How persistence is proven (documented check)

The requirement: *create rows → restart app and container → rows still there.*

Because Postgres runs with a **named volume** (`db_data` in compose), its
data lives outside any container lifecycle.

```bash
# 1. Start the stack
docker compose up --build -d

# 2. Create a few rows
curl -s -X POST http://localhost:8000/tasks \
     -H 'Content-Type: application/json' -d '{"title":"Persistence proof"}'
curl -s http://localhost:8000/tasks           # note the row is there

# 3. Restart ONLY the app container (data must survive)
docker compose restart app
curl -s http://localhost:8000/tasks           # row STILL there ✅

# 4. Blow away and recreate BOTH containers — but keep the volume
docker compose down
docker compose up -d
curl -s http://localhost:8000/tasks           # row STILL there ✅

# 5. (optional nuclear test) confirm the volume is on disk
docker volume ls | grep taskapi
```

**Result:** rows created via the API survive app restarts, container
recreations, and `docker compose down` — because they live in Postgres, whose
data is persisted by the `db_data` named volume. Contrast with
`repo_from_env()` picking the in-memory store (`DATABASE_URL` unset): there
everything is lost on restart, which is exactly the "demo" behaviour A3 is
meant to eliminate.

---

## API reference

Identical to the A2 Task API.

| Method | Path | Description | Status codes |
|--------|------|-------------|--------------|
| GET | `/` | API info incl. active storage backend | 200 |
| GET | `/health` | Health check | 200 |
| GET | `/tasks` | List tasks (`?done=`, `?search=`) | 200 |
| GET | `/tasks/{id}` | Get one task | 200, 404 |
| POST | `/tasks` | Create task `{"title": "..."}` | 201, 400 |
| PUT | `/tasks/{id}` | Update task `{"title","done"}` | 200, 400, 404 |
| DELETE | `/tasks/{id}` | Delete task | 204, 404 |
| GET | `/stats` | Task statistics | 200 |

---

## Running the tests (local, no Docker needed)

The unit tests exercise the full API against the **in-memory** backend so they
run anywhere (no Postgres required). The service/routes are the same code that
runs in Docker.

```bash
python -m venv venv
venv\Scripts\activate        # or: source venv/bin/activate (Linux/macOS)

pip install -r requirements.txt
cd app
python -m pytest ../test_api.py -q
```

Expected: `11 passed`.

---

## Stretch work (optional)

- **Add Redis to the compose file and ping it from the app** — see
  `docker-compose.yml`; a `redis` service can be added alongside `db` and
  pinged with `redis-py`.
- **Index + `EXPLAIN ANALYZE`** — `db/init.sql` already creates
  `idx_tasks_title`. To compare before/after on the seeded table:

  ```sql
  EXPLAIN ANALYZE SELECT * FROM tasks WHERE title ILIKE '%groc%';
  -- drop index:  DROP INDEX IF EXISTS idx_tasks_title;  → re-run
  -- recreate:    CREATE INDEX idx_tasks_title ON tasks (title);
  EXPLAIN ANALYZE SELECT * FROM tasks WHERE title ILIKE '%groc%';
  ```

  The indexed `ILIKE`/`ORDER BY title` query uses the index; without it Postgres
  falls back to a sequential scan.
