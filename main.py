from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import sqlite3

app = FastAPI(
    title="Task API",
    description="A simple CRUD API for managing to-do tasks.",
    version="2.0",
)

DB_PATH = "tasks.db"


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create table and seed data if needed."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("Buy groceries", False),
                ("Read a book", True),
                ("Clean the house", False),
            ],
        )
    conn.commit()
    conn.close()


init_db()


class TaskCreate(BaseModel):
    title: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


@app.get("/")
def root():
    return {"name": "Task API", "version": "2.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks(
    done: Optional[bool] = Query(None, description="Filter by completion status"),
    search: Optional[str] = Query(None, description="Search tasks by title"),
):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT id, title, done FROM tasks"
    conditions = []
    params = []
    if done is not None:
        conditions.append("done = ?")
        params.append(int(done))
    if search:
        conditions.append("title LIKE ?")
        params.append(f"%{search}%")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r["id"], "title": r["title"], "done": bool(r["done"])} for r in rows]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate):
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (payload.title.strip(), 0))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": new_id, "title": payload.title.strip(), "done": False}


@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    if payload.title is None and payload.done is None:
        raise HTTPException(
            status_code=400, detail="At least title or done must be provided"
        )
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    if payload.title is not None:
        if not payload.title.strip():
            conn.close()
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        cursor.execute("UPDATE tasks SET title = ? WHERE id = ?", (payload.title.strip(), task_id))
    if payload.done is not None:
        cursor.execute("UPDATE tasks SET done = ? WHERE id = ?", (int(payload.done), task_id))
    conn.commit()
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return None


@app.get("/stats")
def stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tasks")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE done = 1")
    done_count = cursor.fetchone()[0]
    conn.close()
    return {"total": total, "done": done_count, "open": total - done_count}
