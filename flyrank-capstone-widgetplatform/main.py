"""Embeddable Widget & Lead-Capture Platform — FastAPI.

Endpoints:
  * Admin (api-key protected):
    POST   /admin/tenants            create tenant
    POST   /admin/tenants/{t}/widgets  create widget
    GET    /admin/tenants/{t}/widgets  list widgets (tenant isolated)
    PATCH  /admin/widgets/{id}        update widget -> bumps version
    GET    /admin/tenants/{t}/stats   dashboard stats
  * Public:
    GET    /w/{widget_id}.js          cached, versioned widget bundle
    POST   /lead                      public submission (CORS, validate, abuse)
"""

import json
import os
import time
import uuid

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from abuse import HONEYPOT_FIELD, RateLimiter, is_honeypot_filled, validate_lead
from geo import FakeGeoResolver
from widget_store import SafeSideEffects, WidgetStore

# ---------------------------------------------------------------------------
# Wiring
# ---------------------------------------------------------------------------
DB_PATH = os.getenv("DATABASE_PATH", "").strip() or ":memory:"
store = WidgetStore(DB_PATH)
geo = FakeGeoResolver()  # switch to GeoResolver() for real providers
side_effects = SafeSideEffects()

MASTER_API_KEY = os.getenv("MASTER_API_KEY", "dev-master-key")

# per-IP and per-widget rate limits
ip_limiter = RateLimiter(rate_per_min=30, burst=30)
widget_limiter = RateLimiter(rate_per_min=60, burst=60)

app = FastAPI(title="Embeddable Widget & Lead-Capture Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # widgets are embedded on arbitrary customer sites
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas at the boundary
# ---------------------------------------------------------------------------
class CreateTenantRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CreateWidgetRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    title: str | None = Field(default=None, max_length=200)
    button_label: str = Field(default="Submit", max_length=50)
    config: dict = Field(default_factory=dict)


class UpdateWidgetRequest(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    title: str | None = Field(default=None, max_length=200)
    button_label: str | None = Field(default=None, max_length=50)
    config: dict | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _require_admin(x_api_key: str = Header(default="", alias="X-Api-Key")):
    if x_api_key != MASTER_API_KEY:
        raise HTTPException(status_code=401, detail="invalid or missing API key")


def _log_submission(widget_id, ip, email, honey, accepted, reason=""):
    with store.tx() as c:
        c.execute(
            """INSERT INTO submissions_log
               (widget_id, ip_address, email, honey, accepted, reason, created_at)
               VALUES (?,?,?,?,?,?,?)""",
            (widget_id, ip, (email or "")[:120], int(honey), int(accepted), reason, int(time.time())),
        )


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("X-Forwarded-For")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else ""


# ---------------------------------------------------------------------------
# Admin routes (tenant isolation via path tenant_id + auth)
# ---------------------------------------------------------------------------
@app.post("/admin/tenants")
def create_tenant(body: CreateTenantRequest, x_api_key: str = Header(default="", alias="X-Api-Key")):
    _require_admin(x_api_key)
    tenant = store.create_tenant(body.name)
    return {
        "tenant_id": tenant["id"],
        "api_key": tenant["api_key"],  # return once; store hashed going forward
        "name": tenant["name"],
    }


@app.post("/admin/tenants/{tenant_id}/widgets")
def create_widget(tenant_id: str, body: CreateWidgetRequest, x_api_key: str = Header(default="", alias="X-Api-Key")):
    _require_admin(x_api_key)
    if not store.get_tenant(tenant_id):
        raise HTTPException(status_code=404, detail="tenant not found")
    widget = store.create_widget(
        tenant_id, body.name, body.title, body.button_label, body.config
    )
    return widget


@app.get("/admin/tenants/{tenant_id}/widgets")
def list_widgets(tenant_id: str, x_api_key: str = Header(default="", alias="X-Api-Key")):
    _require_admin(x_api_key)
    return {"tenant_id": tenant_id, "widgets": store.list_widgets(tenant_id)}


@app.patch("/admin/widgets/{widget_id}")
def update_widget(widget_id: str, body: UpdateWidgetRequest, x_api_key: str = Header(default="", alias="X-Api-Key")):
    _require_admin(x_api_key)
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    # need tenant context for isolation: find owning tenant
    widget = store.get_widget(widget_id)
    if not widget:
        raise HTTPException(status_code=404, detail="widget not found")
    updated = store.update_widget(widget_id, widget["tenant_id"], **fields)
    return updated


@app.get("/admin/tenants/{tenant_id}/stats")
def tenant_stats(tenant_id: str, x_api_key: str = Header(default="", alias="X-Api-Key")):
    _require_admin(x_api_key)
    if not store.get_tenant(tenant_id):
        raise HTTPException(status_code=404, detail="tenant not found")
    widgets = store.list_widgets(tenant_id)
    total_leads = 0
    per_widget = {}
    with store.tx() as c:
        for w in widgets:
            row = c.execute(
                "SELECT COUNT(*) AS n FROM leads WHERE widget_id=?", (w["id"],)
            ).fetchone()
            per_widget[w["id"]] = row["n"]
            total_leads += row["n"]
        checked = c.execute(
            """SELECT COUNT(*) AS n, COALESCE(SUM(honey),0) AS honey,
               COALESCE(SUM(case when accepted=0 then 1 else 0 end),0) AS rejected
               FROM submissions_log WHERE widget_id IN (
                 SELECT id FROM widgets WHERE tenant_id=?) AND created_at >= ?""",
            (tenant_id, int(time.time()) - 86400 * 7),
        ).fetchone()
    return {
        "tenant_id": tenant_id,
        "widget_count": len(widgets),
        "total_leads": total_leads,
        "leads_per_widget": per_widget,
        "last_7d": {
            "submissions": checked["n"] or 0,
            "honeypot_blocked": checked["honey"] or 0,
            "rejected": checked["rejected"] or 0,
        },
    }


# ---------------------------------------------------------------------------
# Public widget delivery (cached + versioned)
# ---------------------------------------------------------------------------
@app.get("/w/{widget_id}.js")
def widget_js(widget_id: str):
    result = store.widget_bundle(widget_id)
    if not result:
        raise HTTPException(status_code=404, detail="widget not found")
    version, bundle = result
    return Response(
        content=bundle,
        media_type="text/javascript",
        headers={
            "ETag": f'"{widget_id}-v{version}"',
            "Cache-Control": "public, max-age=300, stale-while-revalidate=600",
            "X-Content-Version": str(version),
        },
    )


# ---------------------------------------------------------------------------
# Public lead submission
# ---------------------------------------------------------------------------
@app.post("/lead")
async def submit_lead(request: Request):
    ip = _client_ip(request)
    form = await request.form()
    data = dict(form)
    widget_id = (data.get("widget_id") or "").strip()
    email = (data.get("email") or "").strip()

    if not widget_id:
        raise HTTPException(status_code=422, detail="widget_id is required")
    widget = store.get_widget(widget_id)
    if not widget:
        _log_submission(widget_id, ip, email, 0, False, "unknown widget")
        raise HTTPException(status_code=404, detail="widget not found")

    # honeypot
    if is_honeypot_filled(data):
        _log_submission(widget_id, ip, email, 1, False, "honeypot")
        # pretend success to the bot
        return {"ok": True, "lead_id": ""}

    # rate limiting (per-IP and per-widget)
    if not ip_limiter.allow(f"ip:{ip}") or not widget_limiter.allow(f"w:{widget_id}"):
        _log_submission(widget_id, ip, email, 0, False, "rate limited")
        raise HTTPException(
            status_code=429,
            detail="too many submissions, try again later",
            headers={"Retry-After": "5"},
        )

    # boundary validation
    ok, reason = validate_lead(data)
    if not ok:
        _log_submission(widget_id, ip, email, 0, False, reason)
        raise HTTPException(status_code=422, detail=reason)

    # geo enrichment (degrades to {} on failure)
    geo_info = geo.resolve(ip)

    lead_id = uuid.uuid4().hex
    with store.tx() as c:
        c.execute(
            """INSERT INTO leads (id, widget_id, tenant_id, email, name, payload, ip_address, geo, created_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                lead_id, widget_id, widget["tenant_id"], email,
                data.get("name") or None, json.dumps(data)[:4000], ip,
                json.dumps(geo_info), int(time.time()),
            ),
        )
    _log_submission(widget_id, ip, email, 0, True, "accepted")

    # safe side effects: never block on failure
    side_effects.notify(
        {"email": email, "name": data.get("name"), "widget_id": widget_id, "geo": geo_info}
    )

    return {"ok": True, "lead_id": lead_id}
