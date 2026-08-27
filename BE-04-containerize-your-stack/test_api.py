"""Tests for the Task API (BE-04).

These run against the IN-MEMORY repository so they work locally without
Docker/Postgres. The same routes/services are exercised; swapping to the
Postgres repository is covered in README.md (persistence check via
`docker compose up`).

Run:  pytest test_api.py
"""

import os

os.environ.pop("DATABASE_URL", None)

from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


def test_root_reports_backend():
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Task API"
    assert "storage" in data


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_list_tasks_seeded():
    r = client.get("/tasks")
    assert r.status_code == 200
    tasks = r.json()
    assert len(tasks) >= 3
    assert {"title", "done", "created_at", "updated_at"} <= set(tasks[0].keys())


def test_create_task():
    r = client.post("/tasks", json={"title": "Test task"})
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "Test task"
    assert body["done"] is False
    assert body["id"] > 0


def test_create_task_missing_title_is_400():
    r = client.post("/tasks", json={"title": "   "})
    assert r.status_code == 400


def test_get_single_task():
    created = client.post("/tasks", json={"title": "Get me"}).json()
    r = client.get(f"/tasks/{created['id']}")
    assert r.status_code == 200
    assert r.json()["title"] == "Get me"


def test_get_missing_task_is_404():
    assert client.get("/tasks/999999").status_code == 404


def test_update_task():
    created = client.post("/tasks", json={"title": "Update me"}).json()
    r = client.put(f"/tasks/{created['id']}", json={"done": True})
    assert r.status_code == 200
    assert r.json()["done"] is True


def test_delete_task_returns_204():
    created = client.post("/tasks", json={"title": "Delete me"}).json()
    r = client.delete(f"/tasks/{created['id']}")
    assert r.status_code == 204
    assert client.get(f"/tasks/{created['id']}").status_code == 404


def test_stats():
    r = client.get("/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == body["done"] + body["open"]


def test_filter_done_and_search():
    client.post("/tasks", json={"title": "unique-search-term-xyz"})
    done = client.get("/tasks", params={"done": "true"}).json()
    assert all(t["done"] for t in done)
    found = client.get("/tasks", params={"search": "unique-search-term"}).json()
    assert any("unique-search-term" in t["title"] for t in found)
