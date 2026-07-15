from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Task API", version="1.0")

tasks = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Read a book", "done": True},
    {"id": 3, "title": "Clean the house", "done": False},
]
next_id = 4


class Task(BaseModel):
    title: str
    done: bool = False


class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


@app.get("/")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def get_tasks():
    return tasks


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.post("/tasks", status_code=201)
def create_task(task: Task):
    global next_id
    new_task = {"id": next_id, "title": task.title, "done": task.done}
    tasks.append(new_task)
    next_id += 1
    return new_task


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_update: TaskUpdate):
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    if task_update.title is not None:
        task["title"] = task_update.title
    if task_update.done is not None:
        task["done"] = task_update.done
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    global tasks
    original_len = len(tasks)
    tasks = [t for t in tasks if t["id"] != task_id]
    if len(tasks) == original_len:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
