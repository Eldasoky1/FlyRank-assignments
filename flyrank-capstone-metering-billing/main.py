"""Usage Metering & Billing Engine — FastAPI application.

Endpoints (see capstone.yaml):
  * POST /v1/usage                meter a usage event (idempotency-key header)
  * GET  /v1/usage                current usage summary per customer
  * POST /generate                dummy billable endpoint (AI-token usage)
  * POST /webhooks/stripe         verify + dedup + apply Stripe events
  * GET  /health                  liveness
"""

import os

import httpx
from fastapi import FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from billing import StripeBilling
from costing import token_breakdown_to_usages
from metering import (
    InsufficientPayment,
    MeteringService,
    MeteringStore,
    QuotaExceeded,
)
from plans import USAGE_AI_TOKENS, USAGE_API_CALLS

# ---------------------------------------------------------------------------
# App / wiring
# ---------------------------------------------------------------------------
DB_PATH = os.getenv("DATABASE_PATH", "").strip() or ":memory:"
store = MeteringStore(DB_PATH)
service = MeteringService(store)

STRIPE_SECRET = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_demo_secret")
STRIPE_PUBLISHABLE = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

billing = StripeBilling(
    secret_key=STRIPE_SECRET,
    webhook_secret=STRIPE_WEBHOOK_SECRET,
    store=store,
)

app = FastAPI(
    title="Usage Metering & Billing Engine",
    version="1.0.0",
    description="Idempotent metering, quota enforcement, AI-token costing, "
    "Stripe test-mode billing.",
)


# ---------------------------------------------------------------------------
# Schemas (validated at the boundary)
# ---------------------------------------------------------------------------
class MeterUsageRequest(BaseModel):
    customer_id: str = Field(min_length=1, max_length=128)
    usage_type: str = Field(pattern="^(api_calls|ai_tokens)$")
    quantity: int = Field(ge=0, le=1_000_000_000)
    cost_cents: int = Field(default=0, ge=0)


class GenerateRequest(BaseModel):
    customer_id: str = Field(min_length=1, max_length=128)
    prompt: str = Field(min_length=1, max_length=4000)
    model: str = Field(default="default")
    cached_input_tokens: int = Field(default=0, ge=0)
    uncached_input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    reasoning_tokens: int = Field(default=0, ge=0)


class HealthResponse(BaseModel):
    status: str
    stripe_connected: bool


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "stripe_connected": bool(STRIPE_SECRET)}


@app.post("/v1/usage")
def meter_usage(
    body: MeterUsageRequest,
    idempotency_key: str = Header(default="", alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Idempotency-Key header is required",
        )
    if body.quantity == 0:
        return {"customer_id": body.customer_id, "recorded": True, "quantity": 0, "ledger": []}
    try:
        result = service.record_usage(
            customer_id=body.customer_id,
            usage_type=body.usage_type,
            idempotency_key=idempotency_key,
            quantity=body.quantity,
            cost_cents=body.cost_cents,
        )
    except InsufficientPayment as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    except QuotaExceeded as exc:
        headers = {"Retry-After": "2592000"}  # next month reset
        raise HTTPException(status_code=exc.status_code, detail=str(exc), headers=headers)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {
        "customer_id": body.customer_id,
        "usage_type": body.usage_type,
        "recorded": result["recorded"],
        "idempotent": result.get("idempotent", False),
        "quantity": body.quantity,
    }


@app.get("/v1/usage")
def usage_summary(customer_id: str):
    return service.usage_summary(customer_id)


@app.post("/generate")
async def generate(body: GenerateRequest):
    """Dummy billable endpoint: records one API call + AI-token usage."""
    idem = f"gen-{body.customer_id}-{hash(body.prompt) & 0xFFFFFFFF:x}"
    breakdown = token_breakdown_to_usages(
        cached_input_tokens=body.cached_input_tokens,
        uncached_input_tokens=body.uncached_input_tokens,
        output_tokens=body.output_tokens,
        reasoning_tokens=body.reasoning_tokens,
    )
    try:
        service.record_usage(
            body.customer_id, USAGE_API_CALLS, idempotency_key=idem, quantity=1, cost_cents=1
        )
        service.record_usage(
            body.customer_id, USAGE_AI_TOKENS, idempotency_key=idem, quantity=breakdown["total_tokens"],
            cost_cents=breakdown["cost_cents"],
        )
    except InsufficientPayment as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    except QuotaExceeded as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {
        "customer_id": body.customer_id,
        "tokens": breakdown,
        "message": "generated (billed)",
    }


@app.get("/checkout")
def checkout_start(customer_id: str):
    """Create a Stripe Checkout session (test mode only)."""
    if not STRIPE_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Stripe test keys not configured (see .env.example)",
        )
    session = billing.create_checkout_session(
        customer_id=customer_id,
        price_id=os.getenv("STRIPE_PRO_PRICE_ID", ""),
        success_url="http://localhost:8000/success",
        cancel_url="http://localhost:8000/cancel",
    )
    return {"checkout_url": session.url, "publishable": STRIPE_PUBLISHABLE}


@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    header = request.headers.get("Stripe-Signature", "")
    if not header:
        raise HTTPException(status_code=400, detail="missing Stripe-Signature")
    try:
        result = billing.handle_event(payload, header)
    except ValueError as exc:
        # Forged / invalid signature -> 400
        raise HTTPException(status_code=400, detail=str(exc))
    return result
