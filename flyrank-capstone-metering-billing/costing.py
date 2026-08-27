"""AI token cost rules.

Rules implemented (per the capstone brief):
  * cached prompt input is cheaper than uncached prompt input
  * reasoning tokens are billed at the output rate
  * categories / metadata never add cost

All prices are per 1,000,000 tokens, stored in integer cents per token as a
fractional rate. We do the money math in integer cents for the final figure.
"""

from dataclasses import dataclass

# Convenient exponent of 1e6
PER_MILLION = 1_000_000


@dataclass(frozen=True)
class TokenCost:
    """Per-token costs in *fractional* cents (priced per 1M tokens).

    e.g. 0.10 usd / 1M = 10 cents / 1M tokens -> 1e-5 cents / token.
    We keep them as this per-million scale and divide once, but we ballpark
    via integer micro-cents to avoid float drift where it matters.
    """

    cached_input_usd_per_m: float
    uncached_input_usd_per_m: float
    output_usd_per_m: float


DEFAULT_TOKEN_COST = TokenCost(
    cached_input_usd_per_m=0.10,
    uncached_input_usd_per_m=0.40,
    output_usd_per_m=1.20,
)


def _usd_per_m_to_cents_per_token(usd_per_m: float) -> float:
    # usd_per_m dollars / 1e6 tokens -> cents / token
    return (usd_per_m * 100) / PER_MILLION


def calculate_token_cost_usd(
    cached_input_tokens: int,
    uncached_input_tokens: int,
    output_tokens: int,
    reasoning_tokens: int = 0,
    cost: TokenCost = DEFAULT_TOKEN_COST,
) -> float:
    """Return monetary cost in integer cents (as an int).

    * cached input  -> cached_input rate (cheaper)
    * uncached input -> uncached_input rate
    * output + reasoning tokens -> output rate (reasoning billed like output)
    * categories/metadata contributes nothing (no param -> no cost)
    """
    cents = 0.0
    cents += cached_input_tokens * _usd_per_m_to_cents_per_token(cost.cached_input_usd_per_m)
    cents += uncached_input_tokens * _usd_per_m_to_cents_per_token(cost.uncached_input_usd_per_m)
    cents += (output_tokens + reasoning_tokens) * _usd_per_m_to_cents_per_token(cost.output_usd_per_m)
    return int(round(cents))


def token_breakdown_to_usages(
    cached_input_tokens: int,
    uncached_input_tokens: int,
    output_tokens: int,
    reasoning_tokens: int = 0,
    cost: TokenCost = DEFAULT_TOKEN_COST,
) -> dict:
    """Return a breakdown suitable for metering / a usage record."""
    total_tokens = (
        cached_input_tokens
        + uncached_input_tokens
        + output_tokens
        + reasoning_tokens
    )
    cents = calculate_token_cost_usd(
        cached_input_tokens,
        uncached_input_tokens,
        output_tokens,
        reasoning_tokens,
        cost,
    )
    return {
        "total_tokens": total_tokens,
        "cached_input_tokens": cached_input_tokens,
        "uncached_input_tokens": uncached_input_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "cost_cents": cents,
    }
