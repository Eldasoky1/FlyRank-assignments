"""Durable scheduler: survives crashes without double-posting.

SQLite-backed queue. Each job is claimed transactionally: UPDATE ... SET
status='running', claimed_at=now WHERE id=? AND status='queued'. A crash mid-
publish leaves the job 'running'; on restart, stale 'running' jobs (older than
STALE_SECS) are reclaimed. Double-posting is prevented both by the claim
(atomic) and by the publisher's content-hash idempotency.
"""

from __future__ import annotations

import os
import sqlite3
import threading
import time
import uuid

DB_PATH = os.getenv("SOCIAL_DB", os.path.join(os.path.dirname(__file__), "tasks.db"))
STALE_SECS = int(os.getenv("STALE_SECS", "300"))


def _conn(db_path=None):
    c = sqlite3.connect(db_path or DB_PATH, timeout=10, isolation_level=None)
    c.row_factory = sqlite3.Row
    return c


SCHEMA = """
CREATE TABLE IF NOT EXISTS publish_jobs (
    id            TEXT PRIMARY KEY,
    platform      TEXT NOT NULL,
    content_hash  TEXT NOT NULL,
    account       TEXT,
    text          TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'queued',   -- queued|running|done|failed
    external_id   TEXT,
    error         TEXT,
    created_at    REAL,
    claimed_at    REAL,
    updated_at    REAL,
    UNIQUE(platform, content_hash)
);
"""


class Scheduler:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self._init_db()
        self._lock = threading.Lock()

    def _init_db(self):
        c = _conn(self.db_path)
        c.executescript(SCHEMA)
        c.close()

    def enqueue(self, platform, text, account, assets=None):
        h = _content_hash(text, assets)
        c = _conn(self.db_path)
        job_id = uuid.uuid4().hex[:8]
        try:
            # idempotent queue: same platform+content_hash already queued/done
            row = c.execute(
                "SELECT id FROM publish_jobs WHERE platform=? AND content_hash=?",
                (platform, h),
            ).fetchone()
            if row:
                return row["id"], "already_queued"
            c.execute(
                "INSERT INTO publish_jobs (id,platform,content_hash,account,text,status,created_at)"
                " VALUES (?,?,?,?,?,'queued',?)",
                (job_id, platform, h, account, text, time.time()),
            )
            c.commit()
            return job_id, "queued"
        finally:
            c.close()

    def _claim(self, job_id):
        """Atomic claim: only succeeds if status is queued."""
        c = _conn(self.db_path)
        try:
            cur = c.execute(
                "UPDATE publish_jobs SET status='running', claimed_at=?, updated_at=?"
                " WHERE id=? AND status='queued'",
                (time.time(), time.time(), job_id),
            )
            c.commit()
            return cur.rowcount == 1
        finally:
            c.close()

    def _reclaim_stale(self):
        """Reclaim jobs stuck in running from a previous crash."""
        c = _conn(self.db_path)
        try:
            cutoff = time.time() - STALE_SECS
            cur = c.execute(
                "UPDATE publish_jobs SET status='queued', claimed_at=NULL"
                " WHERE status='running' AND claimed_at < ?",
                (cutoff,),
            )
            c.commit()
            return cur.rowcount
        finally:
            c.close()

    def publish_due(self, publisher, account_oauth=False):
        """Claim + publish due queued jobs (called by loop / manually)."""
        self._reclaim_stale()
        c = _conn(self.db_path)
        try:
            rows = c.execute(
                "SELECT * FROM publish_jobs WHERE status='queued' ORDER BY created_at"
            ).fetchall()
            results = []
            for row in rows:
                if not self._claim(row["id"]):
                    continue
                try:
                    oauth = account_oauth if account_oauth else {"account_id": row["account"]}
                    res = publisher.send(oauth, {"text": row["text"]})
                    c.execute(
                        "UPDATE publish_jobs SET status='done', external_id=?, updated_at=?"
                        " WHERE id=?",
                        (res.external_id, time.time(), row["id"]),
                    )
                    results.append({"id": row["id"], "platform": row["platform"],
                                    "status": "done", "external_id": res.external_id})
                except Exception as exc:  # noqa: BLE001
                    c.execute(
                        "UPDATE publish_jobs SET status='failed', error=?, updated_at=?"
                        " WHERE id=?",
                        (str(exc), time.time(), row["id"]),
                    )
                    results.append({"id": row["id"], "platform": row["platform"],
                                    "status": "failed", "error": str(exc)})
            c.commit()
            return results
        finally:
            c.close()

    def get(self, job_id):
        c = _conn(self.db_path)
        try:
            row = c.execute("SELECT * FROM publish_jobs WHERE id=?", (job_id,)).fetchone()
            return dict(row) if row else None
        finally:
            c.close()

    def mark(self, job_id, status, external_id=None, error=None):
        c = _conn(self.db_path)
        try:
            c.execute(
                "UPDATE publish_jobs SET status=?, external_id=COALESCE(?,external_id),"
                " error=?, updated_at=? WHERE id=?",
                (status, external_id, error, time.time(), job_id),
            )
            c.commit()
        finally:
            c.close()


def _content_hash(text, assets=None):
    import json as _j

    import hashlib

    return hashlib.sha256((text + "|" + _j.dumps(assets or [])).encode("utf-8")).hexdigest()[:16]
