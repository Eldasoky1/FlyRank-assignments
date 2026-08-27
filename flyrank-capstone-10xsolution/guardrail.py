"""Guardrail: validate a plan; reject with explanation instead of silent pass.

Concept: guardrail / validation with rejection + explanation (same principle as
the capstone-3 mismatch guard). A plan must cover measurable objectives, at
least one audience, and at least one channel with assets; otherwise ok=False
with a clear reason.
"""


def validate_plan(plan: dict) -> dict:
    """Return {'ok': bool, 'reasons': [...], 'warnings': [...]}."""
    reasons = []
    warnings = []
    objective = (plan.get("objective") or "").strip()
    if len(objective) < 8:
        reasons.append("objective too vague; write a measurable goal")
    if not plan.get("audiences"):
        reasons.append("no target audience defined")
    channels = plan.get("channels") or []
    if not channels:
        reasons.append("no channels selected")
    for ch in channels:
        if not (ch.get("asset_types") or []):
            warnings.append(f"{ch.get('channel')}: no asset types, check coverage")
    if plan.get("duration_weeks", 0) < 1:
        warnings.append("duration < 1 week; consider pacing")
    return {"ok": not reasons, "reasons": reasons, "warnings": warnings}
