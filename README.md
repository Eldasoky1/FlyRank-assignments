# Task API — W2 Assignment

A simple CRUD API for managing to-do tasks, built with **FastAPI** (Python).

Data lives only in memory — restart the server and tasks reset to the three defaults. This is intentional (a database comes next week).

## Quick Start

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open **http://localhost:8000/docs** for interactive Swagger UI.

## Endpoints

| Method | Path | Description | Status Codes |
|--------|------|-------------|--------------|
| GET | `/` | API info | 200 |
| GET | `/health` | Health check | 200 |
| GET | `/tasks` | List all tasks (optional: `?done=true`, `?search=milk`) | 200 |
| GET | `/tasks/{task_id}` | Get one task | 200, 404 |
| POST | `/tasks` | Create a task (body: `{"title": "..."}`) | 201, 400 |
| PUT | `/tasks/{task_id}` | Update a task (body: `{"title": "...", "done": true}`) | 200, 400, 404 |
| DELETE | `/tasks/{task_id}` | Delete a task | 204, 404 |
| GET | `/stats` | Task statistics (total/done/open) | 200 |

## Example: curl -i

```
HTTP/1.1 201 Created
date: Wed, 15 Jul 2026 21:30:17 GMT
server: uvicorn
content-type: application/json

{"id":4,"title":"Buy milk","done":false}
```

## Swagger UI Screenshot

> Add your screenshot here after opening http://localhost:8000/docs and testing the full CRUD cycle.

## Optional Extras

- **Filtering:** `GET /tasks?done=true` returns only completed tasks
- **Search:** `GET /tasks?search=milk` returns tasks whose title contains "milk"

## The Mortality Experiment

Create a few tasks, restart the server (`Ctrl+C` then re-run `uvicorn main:app --reload`), and `GET /tasks`. The new tasks are gone — only the original three remain. Data stored in memory is lost when the process stops. Databases exist to solve exactly this.

## Tech Stack

- **Python 3.10+**
- **FastAPI** — web framework
- **Uvicorn** — ASGI server
- **Pydantic** — request validation

---

## AI vs Me

### My Prompt

> Build a FastAPI CRUD API for a to-do list. Five endpoints: GET /, GET /health, GET /tasks, GET /tasks/{id}, POST /tasks, PUT /tasks/{id}, DELETE /tasks/{id}. Use an in-memory list with 3 example tasks. Status codes: 200 for reads, 201 for create, 204 for delete, 400 for invalid input, 404 for not found. Validate that POST /tasks has a title field — return 400 if missing. Auto-generate Swagger UI at /docs.

### What the AI Did Better

- **Cleaner code structure** — the AI version is more concise, using `next()` with a generator for lookups instead of a for-loop with `return`/`raise`. It reads more like idiomatic Python.
- **Separation of schemas** — the AI created a single `Task` model for create (with a default `done=False`) instead of making `title` optional and checking manually. This is a cleaner API contract.
- **Uses `global next_id`** — a simpler counter approach instead of my `max()` call on every create.

### What the AI Got Wrong

1. **Missing 400 validation** — POST with `{}` returns `422` (FastAPI's default) instead of the assignment-required `400`. I had to make `title` optional in Pydantic and validate manually to get the right status code.
2. **No filtering or search** — the AI ignored the query parameter extras entirely. GET `/tasks?done=true` returns all tasks unfiltered.
3. **No empty-body validation for PUT** — the AI doesn't check if the request body is empty before updating a task. My version returns 400 if neither `title` nor `done` is provided.
4. **Uses `global` keyword** — while it works, `global` in a web framework is a code smell. In production this would break with multiple workers.

### What My Prompt Forgot to Specify

- I didn't mention that filtering and search were optional extras — the AI correctly ignored them since they weren't in the spec.
- I didn't specify that the 400 should come from my code (not FastAPI's default 422). This led to the biggest difference: the AI relied on Pydantic's built-in validation while I needed custom behavior.
- I forgot to mention the `done` default should be `False` explicitly — the AI chose `done: bool = False` in the model, which is actually the right call.
