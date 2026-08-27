"""Report: render the campaign brief as markdown + HTML deliverable.

Concept: report/artifact generator. The final stage composes all prior stage
outputs into a single, shareable deliverable document.
"""

from __future__ import annotations

import html as _h


def render_markdown(ctx: dict) -> str:
    plan = ctx.get("plan") or {}
    guard = ctx.get("guardrail") or {}
    budget = ctx.get("budget") or {}
    checklist = ctx.get("checklist") or []
    lines = [
        f"# {plan.get('title') or 'Campaign'}",
        "",
        f"**Objective:** {plan.get('objective')}",
        f"**Weeks:** {plan.get('duration_weeks', 1)}",
        "",
        "## Guardrail",
        ("PASS" if guard.get("ok") else "FAIL") + " :: " + (", ".join(guard.get("reasons") or []) or "ok"),
        "",
        "## Budget",
        f"Total: ${budget.get('grand_total_usd', 0):.2f}",
        "",
        "## Checklist",
    ]
    for item in checklist:
        lines.append(f"- [ ] {item['channel']}: {item['asset']} (owner {item['owner']})")
    return "\n".join(lines)


def render_report(ctx: dict) -> str:
    md = render_markdown(ctx)
    title = (ctx.get("plan") or {}).get("title", "Campaign")
    body = _h.escape(md).replace("\n", "<br>")
    return f"<html><head><title>{_h.escape(title)}</title></head><body>{body}</body></html>"
