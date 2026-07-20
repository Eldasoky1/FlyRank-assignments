# Task API — W3 · A1

A CRUD API for managing to-do tasks, built with **FastAPI** and **SQLite**.

## Why SQLite

- Built into Python — no extra installation or server needed
- Stores everything in a single file (`tasks.db`)
- Data survives server restarts
- Perfect for small to medium projects

## Where the database is stored

`./tasks.db` in the project root. Created automatically on first run.

## How to start

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open **http://localhost:8000/docs** for Swagger UI.

## Endpoints

| Method | Path | Description | Status Codes |
|--------|------|-------------|--------------|
| GET | `/` | API info | 200 |
| GET | `/health` | Health check | 200 |
| GET | `/tasks` | List all tasks (`?done=true`, `?search=milk`) | 200 |
| GET | `/tasks/{id}` | Get one task | 200, 404 |
| POST | `/tasks` | Create task (`{"title": "..."}`) | 201, 400 |
| PUT | `/tasks/{id}` | Update task (`{"title": "...", "done": true}`) | 200, 400, 404 |
| DELETE | `/tasks/{id}` | Delete task | 204, 404 |
| GET | `/stats` | Task statistics | 200 |

## Database Screenshot

> Add your DB Browser for SQLite screenshot here

## Example SQL query I ran

```sql
SELECT * FROM tasks WHERE done = 1;
```

Returns only completed tasks — same as `GET /tasks?done=true`.

## Optional Extras

- **Search:** `GET /tasks?search=milk` — SQL `LIKE` operator
- **Filter:** `GET /tasks?done=true` — SQL `WHERE` clause
- **Sort:** Tasks ordered alphabetically by title
- **Statistics:** `GET /stats` — uses SQL `COUNT()`
- **Timestamps:** `created_at` and `updated_at` stored for every task
