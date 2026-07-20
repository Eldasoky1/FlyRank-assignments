# Task API — W2 Part 2 Assignment

A simple CRUD API for managing to-do tasks, built with **FastAPI** (Python) and **SQLite**.

Data is now stored in a SQLite database file (`tasks.db`) instead of memory. Restart the server all you want — your tasks survive.

## Quick Start

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open **http://localhost:8000/docs** for interactive Swagger UI.

On first run, `tasks.db` is created automatically with three example tasks.

## Why SQLite

- **No installation needed** — SQLite is built into Python's standard library.
- **Single file** — your entire database lives in `tasks.db` in the project folder.
- **Persistent** — data survives server restarts.
- **Perfect for small projects** — lightweight and fast, with no database server to configure.

## Database Location

The database file is stored at `./tasks.db` in the project root directory. It is created automatically on first run if it does not exist.

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
date: Mon, 20 Jul 2026 12:00:00 GMT
server: uvicorn
content-type: application/json

{"id":4,"title":"Buy milk","done":false}
```

## Database Viewer Screenshot

> Add your screenshot here after opening the database with DB Browser for SQLite and showing the tasks table.

![Database Screenshot](screenshots/database.png)

## Example SQL Query

```sql
SELECT * FROM tasks WHERE done = 1;
```

This returns only completed tasks — the same result as hitting `GET /tasks?done=true`.

## Optional Extras Implemented

- **Filtering:** `GET /tasks?done=true` returns only completed tasks (uses SQL `WHERE done = ?`)
- **Search:** `GET /tasks?search=milk` returns tasks whose title contains "milk" (uses SQL `LIKE`)

## Data Survives Restart

1. Create a task via POST
2. Restart the server (`Ctrl+C` then re-run)
3. Run GET /tasks — the task is still there

This is the key difference from Week 1's in-memory version.

## Tech Stack

- **Python 3.10+**
- **FastAPI** — web framework
- **Uvicorn** — ASGI server
- **Pydantic** — request validation
- **SQLite** — built-in Python database (no external server needed)

---

## AI vs Me

### My Prompt

> Update the CRUD API to use SQLite instead of an in-memory list. Keep all endpoints and behavior exactly the same. Create the tasks table with id, title, and done columns. Seed three tasks on first run only.

### What the AI Did Better

- **Clean separation of concerns** — database logic uses helper functions (`get_db`, `init_db`) that keep SQL out of route handlers.
- **Proper parameterized queries** — all SQL uses `?` placeholders instead of string interpolation, preventing SQL injection.
- **Row factory** — uses `sqlite3.Row` to access columns by name, making code more readable.

### What the AI Got Wrong

- I had to verify the seeded tasks match the originals exactly.
- The `done` column stores `0`/`1` (SQLite booleans) but the API returns `true`/`false` — the conversion is handled in the code.

### What My Prompt Forgot to Specify

- I didn't specify the database file name — the AI chose `tasks.db` which matches the assignment spec.
- I didn't mention the version number change — the AI bumped it to 2.0 which is a nice touch.
