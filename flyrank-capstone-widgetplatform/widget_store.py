"""Widget store + embed snippet + versioned delivery.

Layered: this module is the data/logic layer. HTTP entrypoints live in main.py.
"""

import hashlib
import hmac
import json
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager

# ---------------------------------------------------------------------------
# Aliased imports to keep tenant isolation checks obvious
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS tenants (
    id     TEXT PRIMARY KEY,
    api_key TEXT NOT NULL,
    name   TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS widgets (
    id         TEXT PRIMARY KEY,
    tenant_id  TEXT NOT NULL,
    name       TEXT NOT NULL,
    title      TEXT,
    button_label TEXT DEFAULT 'Submit',
    config     TEXT NOT NULL DEFAULT '{}',
    version    INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
CREATE TABLE IF NOT EXISTS widgets_cache (
    widget_id TEXT PRIMARY KEY,
    version   INTEGER NOT NULL,
    bundle    TEXT NOT NULL,
    updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS leads (
    id         TEXT PRIMARY KEY,
    widget_id  TEXT NOT NULL,
    tenant_id  TEXT NOT NULL,
    email      TEXT NOT NULL,
    name       TEXT,
    payload    TEXT,
    ip_address TEXT,
    geo        TEXT,
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS submissions_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    widget_id  TEXT NOT NULL,
    ip_address TEXT,
    email      TEXT,
    honey      INTEGER NOT NULL DEFAULT 0,
    accepted   INTEGER NOT NULL DEFAULT 0,
    reason     TEXT,
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_leads_widget ON leads(widget_id);
CREATE INDEX IF NOT EXISTS idx_logs_widget_ip ON submissions_log(widget_id, ip_address, created_at);
"""


class WidgetStore:
    def __init__(self, db_path=":memory:"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self._lock = __import__("threading").RLock()

    @contextmanager
    def tx(self):
        with self._lock:
            yield self.conn
            self.conn.commit()

    # ---- tenants ----
    def create_tenant(self, name):
        tenant_id = uuid.uuid4().hex[:12]
        api_key = secrets.token_hex(24)
        with self.tx() as c:
            c.execute(
                "INSERT INTO tenants (id, api_key, name, created_at) VALUES (?,?,?,?)",
                (tenant_id, api_key, name, int(time.time())),
            )
        return self.get_tenant(tenant_id)

    def get_tenant(self, tenant_id):
        with self.tx() as c:
            row = c.execute("SELECT * FROM tenants WHERE id=?", (tenant_id,)).fetchone()
            return dict(row) if row else None

    def tenant_by_api_key(self, api_key):
        with self.tx() as c:
            row = c.execute("SELECT * FROM tenants WHERE api_key=?", (api_key,)).fetchone()
            return dict(row) if row else None

    # ---- widgets ----
    def create_widget(self, tenant_id, name, title=None, button_label="Submit", config=None):
        wid = uuid.uuid4().hex[:12]
        now = int(time.time())
        config = json.dumps(config or {})
        with self.tx() as c:
            c.execute(
                """INSERT INTO widgets (id, tenant_id, name, title, button_label, config, version, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,1,?,?)""",
                (wid, tenant_id, name, title, button_label, config, now, now),
            )
        return self.get_widget(wid)

    def get_widget(self, widget_id, tenant_id=None):
        """Tenant isolation: if tenant_id given, only return widgets owned by it."""
        with self.tx() as c:
            if tenant_id:
                row = c.execute(
                    "SELECT * FROM widgets WHERE id=? AND tenant_id=?",
                    (widget_id, tenant_id),
                ).fetchone()
            else:
                row = c.execute("SELECT * FROM widgets WHERE id=?", (widget_id,)).fetchone()
            return dict(row) if row else None

    def list_widgets(self, tenant_id):
        with self.tx() as c:
            rows = c.execute(
                "SELECT * FROM widgets WHERE tenant_id=? ORDER BY created_at", (tenant_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def update_widget(self, widget_id, tenant_id, **fields):
        widget = self.get_widget(widget_id, tenant_id)
        if not widget:
            return None
        allowed = ("name", "title", "button_label", "config")
        sets, vals = [], []
        for k, v in fields.items():
            if k not in allowed:
                continue
            if k == "config" and isinstance(v, (dict, list)):
                v = json.dumps(v)
            sets.append(f"{k}=?")
            vals.append(v)
        if not sets:
            return self.get_widget(widget_id, tenant_id)
        sets.append("version=version+1")
        sets.append("updated_at=?")
        vals += [int(time.time())]
        with self.tx() as c:
            c.execute(
                f"UPDATE widgets SET {', '.join(sets)} WHERE id=? AND tenant_id=?",
                (*vals, widget_id, tenant_id),
            )
            # invalidate cache for this widget
            c.execute("DELETE FROM widgets_cache WHERE widget_id=?", (widget_id,))
        return self.get_widget(widget_id, tenant_id)

    def delete_widget(self, widget_id, tenant_id):
        with self.tx() as c:
            c.execute("DELETE FROM widgets WHERE id=? AND tenant_id=?", (widget_id, tenant_id))
            c.execute("DELETE FROM widgets_cache WHERE widget_id=?", (widget_id,))

    # ---- versioned, cached widget bundle ----
    def widget_bundle(self, widget_id):
        """Return (version, bundle_html) using the cache when fresh."""
        with self.tx() as c:
            widget = c.execute(
                "SELECT * FROM widgets WHERE id=?", (widget_id,)
            ).fetchone()
            if not widget:
                return None
            cached = c.execute(
                "SELECT bundle, version FROM widgets_cache WHERE widget_id=?", (widget_id,)
            ).fetchone()
            if cached and cached["version"] == widget["version"]:
                return (widget["version"], cached["bundle"])
        bundle = build_embed_bundle(dict(widget))
        with self.tx() as c:
            c.execute(
                """INSERT INTO widgets_cache (widget_id, version, bundle, updated_at)
                   VALUES (?,?,?,?)
                   ON CONFLICT(widget_id) DO UPDATE SET version=excluded.version,
                     bundle=excluded.bundle, updated_at=excluded.updated_at""",
                (widget_id, widget["version"], bundle, int(time.time())),
            )
        return (widget["version"], bundle)


def build_embed_bundle(widget):
    """Self-contained widget HTML (versioned by widget.version + content hash)."""
    payload = {
        "widget_id": widget["id"],
        "title": widget.get("title") or widget.get("name"),
        "button_label": widget.get("button_label", "Submit"),
        "config": json.loads(widget.get("config") or "{}"),
    }
    data = json.dumps(payload, separators=(",", ":"))
    content_hash = hashlib.sha1(data.encode()).hexdigest()[:10]
    return f"""<!-- widget {widget['id']} v{widget['version']} hash:{content_hash} -->
<div class="lead-widget" data-widget="{data}"></div>
<script>
(function(w){{
  var cfg = JSON.parse(w.dataset.widget);
  var f = document.createElement('form');
  f.innerHTML = '<h4></h4><input name="email" type="email" placeholder="you@example.com" required/>' +
    '<input name="name" placeholder="Name"/><input type="text" name="homepage" style="display:none" tabindex="-1" autocomplete="off"/>' +
    '<button type="submit"></button>';
  f.querySelector('h4').textContent = cfg.title || 'Get the latest';
  f.querySelector('button').textContent = cfg.button_label || 'Submit';
  w.appendChild(f);
  f.addEventListener('submit', function(ev){{
    ev.preventDefault();
    var fd = new FormData(f); fd.set('widget_id', cfg.widget_id);
    fetch(cfg.endpoint || '/lead', {{method:'POST', body: fd}});
  }});
}})(document.querySelector('.lead-widget[data-widget]'));
</script>
"""


# ---------------------------------------------------------------------------
# webhook / email "safe side effects" — must never fail the request
# ---------------------------------------------------------------------------
class SafeSideEffects:
    """Send webhooks/emails best-effort. Any failure is swallowed & logged, so
    a broken email/webhook service never blocks lead capture."""

    def __init__(self):
        self.delivered = []

    def notify(self, lead, endpoint=None):
        try:
            if endpoint:
                import httpx

                httpx.post(endpoint, json=lead, timeout=2.0)
            # simulated email
            self.delivered.append(lead["email"])
        except Exception as exc:  # noqa: BLE001 - side effect must not raise
            return {"ok": False, "error": str(exc)}
        return {"ok": True}
