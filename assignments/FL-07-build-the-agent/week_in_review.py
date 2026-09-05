#!/usr/bin/env python3
"""week_in_review.py — the FL-06/FL-07 'weekly review scout' agent.

Agent job (spec section 1): merge my weekly log + fresh industry feeds into one
mentor-review-ready "week in review" brief, picking this week's topics from how
last week's runs went — then STOP at a signoff gate. Never submits anything.

Implements the FL-06 spec verbatim (eval cases E1-E6 enforced in --selftest):
  E1 thin-run recovery, E2 topic drift, E3 hallucination guard, E4 signoff gate,
  E5 format contract, E6 feed resilience.

Data/tool connections used (>= 1 required by FL-07):
  - live HTTPS RSS feeds (external service) via weekly_brief.gather
  - filesystem read of this repo's agent-run.jsonl (prior run history)
  - filesystem write of the brief + run log under --out

Usage:
    python week_in_review.py --log weekly-log-2026-09-04.md
    python week_in_review.py --log weekly-log.md --topic "agents;mcp"   # E2 drift override
    python week_in_review.py --selftest                                 # runs eval E1-E6
    python week_in_review.py --log weekly-log.md --out C:\\temp\\wrev   # controlled out dir

Set ANTHROPIC_API_KEY to enable the model-driven topic branch (spec step 1).
Without a key, topic selection is rule-based and auditable (documented deviation,
see build-log.md entry 4).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FL04 = REPO / "FL-04-automation-workflow"
sys.path.insert(0, str(FL04))

import weekly_brief as wb  # noqa: E402  (reuses GATHER/SYNTHESIZE/FORMAT from FL-04)

DEFAULT_TOPICS = ["LLM;AI", "security;breach", "cloudflare;workers;rust"]
THIN = 3  # runs with fewer kept items than this count as "thin"
SUGGESTIONS = {
    "security;breach": ["appsec;cve;response"],
    "openai;anthropic;model": ["agents;mcp;tool-calling"],
    "LLM;AI": ["regression;eval;automation"],
    "cloudflare;workers;rust": ["edge;wasm;deploy"],
    "developer;api;launch": ["devtools;sdk;launch"],
}


def decide_topics(run_logs: list[dict], override: str | None) -> list[str]:
    """Step 1 - read run history and choose this week's topics (LLM if key, else rules)."""
    if override:
        return [t.strip() for t in re.split(r"[;,]", override) if t.strip()]

    # E1: if last runs were thin, recover with fresh terms instead of repeating a dead topic.
    recent = sorted(run_logs, key=lambda r: r.get("ts", ""), reverse=True)
    for r in recent:
        if r.get("items_kept", 99) < THIN and r.get("topics"):
            for t in r["topics"]:
                if t in SUGGESTIONS:
                    return SUGGESTIONS[t]
            return ["agents;mcp", "appsec;cve", "devtools;launch"]

    # Model-driven branch when a key exists (one API call, spec step 1).
    if os.environ.get("ANTHROPIC_API_KEY"):
        proposed = suggest_topics_llm(recent)
        if proposed:
            return proposed

    return DEFAULT_TOPICS


def suggest_topics_llm(run_logs: list[dict]) -> list[str]:
    """One Claude call proposing 3 topic filters; never leaks the key or logs prompts."""
    stats = {",".join(r.get("topics", [])): r.get("items_kept", -1) for r in run_logs}
    payload = json.dumps(
        {
            "model": "claude-sonnet-4-5",
            "max_tokens": 60,
            "system": wb.DRAFT_SYSTEM,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "You pick 3 topic filters (semicolon-separated) that will return "
                        f"non-empty feed results. Prior runs: {json.dumps(stats)}. "
                        "Output only the filters, e.g. 'agents;mcp;sdk'."
                    ),
                }
            ],
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    raw = data["content"][0]["text"].strip()
    return [t.strip() for t in re.split(r"[;,]", raw) if t.strip()][:3]


def parse_weekly_log(path: Path) -> dict[str, list[str]]:
    """Minimal weekly-log reader: Delivered / Blocked / Next buckets by line keywords."""
    text = path.read_text(encoding="utf-8", errors="replace")
    buckets: dict[str, list[str]] = {"delivered": [], "blocked": [], "next": []}
    for line in text.splitlines():
        line = line.lstrip("- \t")
        low = line.lower()
        if re.match(r"^(delivered|done|shipped|progress)", low):
            buckets["delivered"].append(re.sub(r"^(delivered|done|shipped|progress)[:\s-]+", "", line, flags=re.I))
        elif re.match(r"^(blocked|blocker|bottleneck)", low):
            buckets["blocked"].append(re.sub(r"^(blocked|blocker|bottleneck)[:\s-]+", "", line, flags=re.I))
        elif re.match(r"^(next|priority|up next)", low):
            buckets["next"].append(re.sub(r"^(next|priority|up next)[:\s-]+", "", line, flags=re.I))
    return buckets


def draft(inbox: dict[str, list[str]], items: list[dict], topics: list[str]) -> str:
    """Step 4 - four sections per the spec, FL-02 style target applied in rendering."""
    lines = [
        "# Week in Review",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Summary",
        "",
    ]
    lines += [f"- {d}" for d in inbox["delivered"][:3]] or ["- (no delivered items in weekly log)"]
    lines += ["", "## Blocked", ""]
    lines += inbox["blocked"][:2] or ["- None."]
    lines += ["", "## Signals", ""]
    for it in items:
        flag = " _(needs review)_" if it.get("needs_review") else ""
        lines.append(f"- **{it['title']}** — {it['summary']}{flag}")
        lines.append(f"  Source: {it['feed'].split('/')[2]}")
    lines += ["", "## Next", ""]
    lines += inbox["next"][:1] or ["- (none recorded)"]
    lines += ["", "## Topics used", "", "- " + ", ".join(topics)]
    lines += ["", "## Gate", "", "*Ready for review — not submitted.*"]
    return "\n".join(lines)


def lint(brief: str) -> dict:
    sections = ["# Week in Review", "## Summary", "## Blocked", "## Signals", "## Next", "## Gate"]
    words = len(re.findall(r"\b\w+\b", brief))
    return {
        "missing_sections": [s for s in sections if s not in brief],
        "links_total": brief.count("http"),
        "words": words,
        "under_500": words <= 500,
    }


def run(log_path: Path, override_topic: str | None, out: Path) -> dict:
    print("[1/5] reading run history and choosing topics ...")
    topics = decide_topics(_read_run_log(out), override_topic)
    print(f"      topics -> {topics}")

    print("[2/5] gathering live feeds ...")
    feeds = [u for us in wb.FEEDS.values() for u in us]
    raw, failures = wb.gather(feeds)
    print(f"      fetched {len(raw)} raw items, {len(failures)} feed failure(s)")

    print("[3/5] filtering + synthesizing to signals ...")
    terms = [t.strip() for term in topics for t in term.split(";") if t.strip()]
    raw = [i for i in raw if any(t.lower() in (i["title"] + " " + i["excerpt"]).lower() for t in terms)]
    raw = sorted(raw, key=wb._epoch, reverse=True)[:8]
    items = wb.synthesize(raw)
    print(f"      {len(items)} signal(s) kept")

    print("[4/5] drafting four sections from weekly log + signals ...")
    inbox = parse_weekly_log(log_path)
    brief = draft(inbox, items, topics)

    print("[5/5] linting + writing output; gate: NOT submitted ...")
    lint_res = lint(brief)
    out.mkdir(parents=True, exist_ok=True)
    fname = out / f"week-in-review-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.md"
    fname.write_text(brief, encoding="utf-8")
    with (out / "agent-run.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(
            json.dumps(
                {
                    "topics": topics,
                    "items_kept": len(items),
                    "feeds_failed": len(failures),
                    "lint": lint_res,
                    "file": fname.name,
                    "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                }
            )
            + "\n"
        )
    print(f"      wrote {fname.name} | gate: {lint_res.get('missing_sections') or 'OK'} | words={lint_res['words']}")
    return {
        "topics": topics,
        "items": len(items),
        "feed_failures": failures,
        "lint": lint_res,
        "file": fname.name,
        "gate": "Ready for review - not submitted.",
    }


def _read_run_log(out: Path) -> list[dict]:
    p = out / "agent-run.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def selftest(out: Path) -> int:
    """E1-E6 from the FL-06 spec, with real assertions on build artifacts."""
    import shutil
    import tempfile

    tmp = Path(tempfile.mkdtemp(prefix="wrev_"))
    fails = 0

    # E1 thin-run recovery: a thin run in history must trigger fresh terms.
    got = decide_topics(
        [{"topics": ["security;breach"], "items_kept": 0, "ts": "2026-09-04T00:00:00+00:00"}], None
    )
    ok = got == ["appsec;cve;response"]
    print(f"E1 thin-run recovery        : {'PASS' if ok else 'FAIL'} ({got})")
    fails += 0 if ok else 1

    # E2 topic drift: an override that matches nothing must not crash, and topics are honored.
    log = tmp / "log.md"
    log.write_text("Delivered: merged PR #42\nBlocked: none\nNext: Metering polish\n", encoding="utf-8")
    r = run(log, "keflavik-ropes", tmp / "o")
    ok = r["topics"] == ["keflavik-ropes"] and isinstance(r["items"], int) and "not submitted" in r["gate"].replace("-", "")
    print(f"E2 topic drift (override)   : {'PASS' if ok else 'FAIL'} (topics={r['topics']}, items={r['items']})")
    fails += 0 if ok else 1

    # E3 hallucination guard: 3-word excerpt must be flagged rather than invented upon.
    it = wb.synthesize([{"title": "t", "link": "https://x.example", "date": "", "excerpt": "hi there", "feed": "t"}])[0]
    ok = it.get("needs_review") is True
    print(f"E3 hallucination guard      : {'PASS' if ok else 'FAIL'} (flag={it.get('needs_review')})")
    fails += 0 if ok else 1

    # E4 signoff gate: draft must end with the not-submitted line.
    b = draft({"delivered": ["x"], "blocked": [], "next": []}, [], ["t"])
    ok = b.strip().endswith("*Ready for review — not submitted.*") and "http" not in b.replace("http", "", 1)
    print(f"E4 signoff gate             : {'PASS' if ok else 'FAIL'}")
    fails += 0 if ok else 1

    # E5 format contract: all four human sections present and under 500 words.
    res = lint(b)
    ok = not res["missing_sections"] and res["under_500"]
    print(f"E5 format contract          : {'PASS' if ok else 'FAIL'} ({res})")
    fails += 0 if ok else 1

    # E6 feed resilience: one feed down must not abort the whole run.
    _, failures = wb.gather(["https://does-not-exist.invalid/rss"], timeout=5)
    ok = len(failures) >= 1
    print(f"E6 feed resilience          : {'PASS' if ok else 'FAIL'} ({len(failures)} failure logged)")
    fails += 0 if ok else 1

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\nselftest result: {'ALL PASS' if fails == 0 else f'{fails} FAILURE(S)'}")
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Weekly review scout agent (FL-07).")
    ap.add_argument("--log", help="weekly log markdown file")
    ap.add_argument("--topic", default=None, help="override topic terms (; or , separated)")
    ap.add_argument("--out", default="output", help="output dir")
    ap.add_argument("--selftest", action="store_true", help="run eval cases E1-E6")
    args = ap.parse_args()
    if args.selftest:
        raise SystemExit(selftest(Path(args.out)))
    if not args.log:
        ap.error("--log is required unless --selftest is given")
    result = run(Path(args.log), args.topic, Path(args.out))
    print(json.dumps(result, indent=2, ensure_ascii=False))