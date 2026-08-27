"""Budget projection from a plan (per-channel cost model).

Concept: cost / budget accounting (inherited from the capstone-1 metering
mentality). Each channel+asset gets a unit cost; the projection returns a
per-channel total and a grand total in integer cents.
"""

# per delivery unit cost in cents (arbitrary but stable model)
CHANNEL_UNIT_CENTS = {
    "facebook": 250,
    "instagram": 300,
    "linkedin": 400,
    "youtube": 500,
    "x": 200,
}


def project_budget(plan: dict) -> dict:
    plan = dict(plan)
    channels = plan.get("channels") or []
    rows = []
    grand = 0
    for ch in channels:
        unit = CHANNEL_UNIT_CENTS.get(ch.get("channel"), 200)
        n_assets = max(1, len(ch.get("asset_types") or []))
        total = unit * n_assets
        grand += total
        rows.append({"channel": ch.get("channel"), "assets": ch.get("asset_types") or [],
                     "unit_cents": unit, "total_cents": total})
    return {
        "rows": rows,
        "grand_total_cents": grand,
        "grand_total_usd": round(grand / 100, 2),
    }
