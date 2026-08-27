"""Asset checklist from a plan (ownership + status).

Concept: deterministic transformation of structured plan -> an actionable
checklist with explicit ownership and status, ready for a team to execute.
"""


def build_checklist(plan: dict) -> list[dict]:
    items = []
    for ch in (plan.get("channels") or []):
        for asset in (ch.get("asset_types") or []):
            items.append({
                "id": f"{ch.get('channel')}/{asset}".replace(" ", "-"),
                "channel": ch.get("channel"),
                "asset": asset,
                "owner": ch.get("channel"),
                "status": "todo",
            })
    return items
