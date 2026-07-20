from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import sqlite3
from datetime import datetime

app = FastAPI(
    title="Task API",
    description="A simple CRUD API for managing to-do tasks with SQLite.",
    version="2.0",
)

DB_PATH = "tasks.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    if count == 0:
        now = datetime.now().isoformat()
        cursor.executemany(
            "INSERT INTO tasks (title, done, created_at, updated_at) VALUES (?, ?, ?, ?)",
            [
                ("Buy groceries", False, now, now),
                ("Read a book", True, now, now),
                ("Clean the house", False, now, now),
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
    return {"name": "Task API", "version": "2.0", "endpoints": ["/tasks", "/stats"]}


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
    query = "SELECT id, title, done, created_at, updated_at FROM tasks"
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
    query += " ORDER BY title"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "done": bool(r["done"]),
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, done, created_at, updated_at FROM tasks WHERE id = ?",
        (task_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate):
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    now = datetime.now().isoformat()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, done, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (payload.title.strip(), 0, now, now),
    )
    new_id = cursor.lastrowid
    conn.commit()
    cursor.execute(
        "SELECT id, title, done, created_at, updated_at FROM tasks WHERE id = ?",
        (new_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


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
        cursor.execute(
            "UPDATE tasks SET title = ?, updated_at = ? WHERE id = ?",
            (payload.title.strip(), datetime.now().isoformat(), task_id),
        )
    if payload.done is not None:
        cursor.execute(
            "UPDATE tasks SET done = ?, updated_at = ? WHERE id = ?",
            (int(payload.done), datetime.now().isoformat(), task_id),
        )
    conn.commit()
    cursor.execute(
        "SELECT id, title, done, created_at, updated_at FROM tasks WHERE id = ?",
        (task_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


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
