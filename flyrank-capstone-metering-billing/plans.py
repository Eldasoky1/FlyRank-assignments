"""Plan definitions and pricing data for the usage metering & billing engine.

All money is represented as integer cents. Never use floats for money.
"""

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Usage types
# ---------------------------------------------------------------------------
USAGE_API_CALLS = "api_calls"
USAGE_AI_TOKENS = "ai_tokens"

USAGE_TYPES = (USAGE_API_CALLS, USAGE_AI_TOKENS)


# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Plan:
    slug: str
    name: str
    # quota per monthly billing cycle, keyed by usage type
    quota: dict
    # price in integer cents per unit, keyed by usage type (0 = free)
    price_per_unit_cents: dict


PLANS = {
    "free": Plan(
        slug="free",
        name="Free",
        quota={USAGE_API_CALLS: 100, USAGE_AI_TOKENS: 0},
        price_per_unit_cents={USAGE_API_CALLS: 0, USAGE_AI_TOKENS: 0},
    ),
    "pro": Plan(
        slug="pro",
        name="Pro",
        quota={USAGE_API_CALLS: 100_000, USAGE_AI_TOKENS: 1_000_000},
        price_per_unit_cents={USAGE_API_CALLS: 1, USAGE_AI_TOKENS: 0},
    ),
}

# Paid plans require an active subscription / payment method.
PAID_PLANS = {"pro"}


def get_plan(slug: str) -> Plan:
    if slug not in PLANS:
        raise ValueError(f"unknown plan: {slug!r}")
    return PLANS[slug]


def is_paid(plan_slug: str) -> bool:
    return plan_slug in PAID_PLANS
