"""Repository layer for the Task API.

The whole point of this assignment is to prove that "switching storage
only touches ONE FILE". Routes and service logic never change; they talk
to a small `TaskRepository` interface. Today there are two concrete
implementations:

- `InMemoryTaskRepository`  -> a plain dict (the original A2 demo store)
- `PostgresTaskRepository`  -> real Postgres behind the same interface

Swapping storage is a single line in `main.py`:
    repo = repo_from_env()   # picks the implementation from DATABASE_URL
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

import psycopg
from psycopg.rows import dict_row


class Task:
    """A single to-do task (value object, schema-independent)."""

    def __init__(self, id, title, done, created_at, updated_at):
        self.id = id
        self.title = title
        self.done = done
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "done": bool(self.done),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class TaskRepository(ABC):
    """Interface both storage backends implement. Service/routes depend on
    this, never on a concrete class."""

    @abstractmethod
    def list(self, done: Optional[bool] = None, search: Optional[str] = None) -> list:
        ...

    @abstractmethod
    def get(self, task_id: int) -> Optional[Task]:
        ...

    @abstractmethod
    def create(self, title: str) -> Task:
        ...

    @abstractmethod
    def update(self, task_id: int, title: Optional[str], done: Optional[bool]) -> Optional[Task]:
        ...

    @abstractmethod
    def delete(self, task_id: int) -> bool:
        ...

    @abstractmethod
    def stats(self) -> dict:
        ...


class InMemoryTaskRepository(TaskRepository):
    """Demo store: a dict that lives only in process memory.
    Data is LOST on restart by design."""

    def __init__(self):
        self._store = {}
        self._seq = 0

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def _from(self, t):
        return Task(t["id"], t["title"], t["done"], t["created_at"], t["updated_at"])

    def _seed(self):
        for title in ["Buy groceries", "Read a book", "Clean the house"]:
            self.create(title)
        self._store[2]["done"] = True

    def list(self, done=None, search=None):
        rows = [self._from(t) for t in self._store.values()]
        if done is not None:
            rows = [t for t in rows if t.done == done]
        if search:
            rows = [t for t in rows if search.lower() in t.title.lower()]
        return sorted(rows, key=lambda t: t.title.lower())

    def get(self, task_id):
        t = self._store.get(task_id)
        return self._from(t) if t else None

    def create(self, title):
        self._seq += 1
        now = self._now()
        self._store[self._seq] = {
            "id": self._seq,
            "title": title.strip(),
            "done": False,
            "created_at": now,
            "updated_at": now,
        }
        return self._from(self._store[self._seq])

    def update(self, task_id, title=None, done=None):
        t = self._store.get(task_id)
        if not t:
            return None
        if title is not None:
            t["title"] = title.strip()
        if done is not None:
            t["done"] = done
        t["updated_at"] = self._now()
        return self._from(t)

    def delete(self, task_id):
        return self._store.pop(task_id, None) is not None

    def stats(self):
        rows = list(self._store.values())
        total = len(rows)
        done_count = sum(1 for r in rows if r["done"])
        return {"total": total, "done": done_count, "open": total - done_count}


class PostgresTaskRepository(TaskRepository):
    """Production store: real Postgres behind the same interface."""

    def __init__(self, dsn: str):
        self._dsn = dsn
        self._conn = psycopg.connect(dsn, row_factory=dict_row)

    def _execute(self, sql, params=None):
        with self._conn.cursor() as cur:
            cur.execute(sql, params or ())
            try:
                return cur.fetchall()
            except psycopg.ProgrammingError:
                self._conn.rollback()
                return []

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def _rows_to_tasks(self, rows):
        return [
            Task(r["id"], r["title"], r["done"], r["created_at"], r["updated_at"])
            for r in rows
        ]

    def list(self, done=None, search=None):
        sql = "SELECT id, title, done, created_at, updated_at FROM tasks"
        clauses, params = [], []
        if done is not None:
            clauses.append("done = %s")
            params.append(done)
        if search:
            clauses.append("title ILIKE %s")
            params.append(f"%{search}%")
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY title"
        return self._rows_to_tasks(self._execute(sql, params))

    def get(self, task_id):
        rows = self._execute(
            "SELECT id, title, done, created_at, updated_at FROM tasks WHERE id = %s",
            (task_id,),
        )
        return self._rows_to_tasks(rows)[0] if rows else None

    def create(self, title):
        now = self._now()
        self._execute(
            "INSERT INTO tasks (title, done, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s) RETURNING id, title, done, created_at, updated_at",
            (title.strip(), False, now, now),
        )
        self._conn.commit()
        return self.get(self._execute("SELECT LASTVAL() AS id")[0]["id"])

    def update(self, task_id, title=None, done=None):
        existing = self.get(task_id)
        if not existing:
            return None
        new_title = title.strip() if title is not None else existing.title
        new_done = done if done is not None else existing.done
        now = self._now()
        self._execute(
            "UPDATE tasks SET title = %s, done = %s, updated_at = %s WHERE id = %s",
            (new_title, new_done, now, task_id),
        )
        self._conn.commit()
        return self.get(task_id)

    def delete(self, task_id):
        self._execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        self._conn.commit()
        return True

    def stats(self):
        row = self._execute(
            "SELECT COUNT(*) AS total, "
            "COUNT(*) FILTER (WHERE done) AS done "
            "FROM tasks"
        )[0]
        total = row["total"] or 0
        done_count = row["done"] or 0
        return {"total": total, "done": done_count, "open": total - done_count}

    def close(self):
        self._conn.close()


def repo_from_env() -> TaskRepository:
    """Factory: pick the storage backend from the environment.

    - If DATABASE_URL is set -> Postgres (containerized stack)
    - Otherwise            -> in-memory (local quickstart / tests)

    This is the ONLY place that knows about concrete classes, so changing
    storage touches exactly one module.
    """
    dsn = os.getenv("DATABASE_URL")
    if dsn and not dsn.lower().startswith("memory"):
        return PostgresTaskRepository(dsn)
    repo = InMemoryTaskRepository()
    repo._seed()
    return repo
