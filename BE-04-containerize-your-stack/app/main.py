"""Task API — containerized stack (A3 / BE-04).

Routes and service logic are IDENTICAL to the A2 service. The only change
versus A2 is behind the scenes: instead of hard-coding SQLite, the app now
talks to a `TaskRepository` interface (`app/repository.py`) whose concrete
implementation is chosen by `DATABASE_URL`:

    DATABASE_URL=postgresql://...  -> PostgresTaskRepository (in Docker)
    DATABASE_URL unset             -> InMemoryTaskRepository (local quickstart)

Nothing in this module knows about Postgres or in-memory specifics.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from repository import repo_from_env


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    try:
        REPO.close()
    except AttributeError:
        pass


app = FastAPI(
    title="Task API (Containerized)",
    description="Same CRUD API as A2, now running against Postgres in Docker. "
    "Storage backend is selected purely via the DATABASE_URL env var.",
    version="3.0",
    lifespan=lifespan,
)

REPO = repo_from_env()


class TaskCreate(BaseModel):
    title: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


@app.get("/")
def root():
    return {
        "name": "Task API",
        "version": "3.0",
        "storage": REPO.__class__.__name__,
        "endpoints": ["/tasks", "/stats"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks(
    done: Optional[bool] = Query(None, description="Filter by completion status"),
    search: Optional[str] = Query(None, description="Search tasks by title"),
):
    return [t.to_dict() for t in REPO.list(done=done, search=search)]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = REPO.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task.to_dict()


@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate):
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    return REPO.create(payload.title).to_dict()


@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    if payload.title is None and payload.done is None:
        raise HTTPException(
            status_code=400, detail="At least title or done must be provided"
        )
    if payload.title is not None and not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    task = REPO.update(task_id, title=payload.title, done=payload.done)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task.to_dict()


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    if not REPO.delete(task_id):
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return None


@app.get("/stats")
def stats():
    return REPO.stats()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
