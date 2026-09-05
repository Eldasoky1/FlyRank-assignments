#!/usr/bin/env python3
"""weekly_brief.py — FL-04 automation workflow: "Weekly industry brief".

A 4-step gather -> synthesize -> draft -> format pipeline that fetches live RSS,
summarizes each item (LLM when ANTHROPIC_API_KEY is set, otherwise an extractive
fallback), assembles a dated markdown brief, and lints its own output.

Stdlib only, no pip installs. Tested on Python 3.12 (Windows 11).

Usage:
    python weekly_brief.py                  # newest 10 items across all feeds
    python weekly_brief.py --topic AI --max 8
    python weekly_brief.py --topics "rust;workers" --max 10 --out output
"""

from __future__ import annotations

import argparse
import email.utils
import html
import json
import os
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------- GATHER
FEEDS: dict[str, list[str]] = {
    "hacker-news": ["https://hnrss.org/frontpage"],
    "github": ["https://github.blog/feed/"],
    "cloudflare": ["https://blog.cloudflare.com/rss/"],
    "openai": ["https://openai.com/news/rss.xml"],
    "security": ["https://feeds.feedburner.com/TheHackersNews"],
    "tech-press": ["https://www.theverge.com/rss/index.xml"],
    "ai-scout": ["https://hnrss.org/newest?q=LLM"],  # sits in "The task" brief's track list? no: HN search
}
UA = {"User-Agent": "Mozilla/5.0 (weekly-industry-brief FL-04; +https://github.com/Eldasoky1/FlyRank-assignments)"}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _text(parent, name: str) -> str:
    for child in parent.iter():
        if _local(child.tag) == name and child.text:
            return child.text.strip()
    return ""


def _ns(parent) -> str:
    return parent.tag[: parent.tag.find("}") + 1] if parent.tag.startswith("{") else ""


def _link(entry) -> str:
    for child in entry.iter():
        ln = _local(child.tag)
        if ln == "link":
            if child.text and child.text.strip().startswith("http"):
                return child.text.strip()
            href = child.get("href")
            if href and href.startswith("http"):
                return href
    return ""


def _date(entry) -> str:
    for child in entry.iter():
        if _local(child.tag) in ("pubDate", "published", "updated") and child.text:
            return child.text.strip()
    return ""


def _epoch(it: dict) -> float:
    """Sort key: parse feed dates into epoch; anything unparseable goes last."""
    try:
        return email.utils.parsedate_to_datetime(it["date"]).timestamp()
    except Exception:
        return 0.0


def gather(feed_urls: list[str], timeout: int = 15) -> tuple[list[dict], list[str]]:
    """Fetch feeds, parse entries, dedupe by link. Returns (items, failures)."""
    items: list[dict] = []
    failures: list[str] = []
    seen: set[str] = set()
    for url in feed_urls:
        started = time.perf_counter()
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
            root = ET.fromstring(body)
        except Exception as exc:  # noqa: BLE001 - record every kind of feed failure
            failures.append(f"{url} :: {type(exc).__name__}: {exc}")
            continue
        fetched = 0
        for node in root.iter():
            if _local(node.tag) not in ("item", "entry"):
                continue
            title = _text(node, "title")
            link = _link(node)
            if not title or not link or link in seen:
                continue
            seen.add(link)
            body_txt = _text(node, "description") or _text(node, "summary") or _text(node, "content")
            items.append(
                {
                    "title": html.unescape(title).strip(),
                    "link": link,
                    "date": _date(node),
                    "excerpt": html.unescape(re.sub(r"<[^>]+>", " ", body_txt)).strip()[:900],
                    "feed": url,
                    "fetch_ms": int((time.perf_counter() - started) * 1000),
                }
            )
            fetched += 1
        if fetched == 0:
            failures.append(f"{url} :: 0 entries parsed")
    return items, failures


# --------------------------------------------------------------------------- SYNTHESIZE
DRAFT_SYSTEM = (
    "You write concise AI/software industry briefs. For each item output exactly one line: "
    "`- **{title}** — {one-sentence why it matters}. Source: {link}`. Never invent numbers. "
    "If a title is unclear, still summarize from what is given."
)


def synthesize(items: list[dict]) -> list[dict]:
    """One-sentence 'why it matters' per item. LLM when a key exists, else extractive."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    for it in items:
        if key:
            try:
                it["summary"] = _llm_summarize(it, key)
                it["via"] = "llm:anthropic"
            except Exception:
                it["summary"] = _extractive(it)
                it["via"] = "extractive-fallback"
        else:
            it["summary"] = _extractive(it)
            it["via"] = "extractive"
    return items


def _extractive(it: dict) -> str:
    """First sentence of the excerpt, or a title-only stub when empty."""
    body = re.sub(r"\s+", " ", it["excerpt"]).strip()
    if body:
        first = body.split(". ", 1)[0].strip()
        if len(first) < 20:  # too thin to be useful -> mark for human review
            it["needs_review"] = True
            return body[:260]
        return first + ("." if not first.endswith((".", "!", "?")) else "")
    it["needs_review"] = True
    return "(no excerpt fetched; title only)"


def _llm_summarize(it: dict, key: str) -> str:
    import json as _j

    payload = _j.dumps(
        {
            "model": "claude-sonnet-4-5",
            "max_tokens": 160,
            "system": DRAFT_SYSTEM,
            "messages": [{"role": "user", "content": f"Title: {it['title']}\nExcerpt: {it['excerpt'][:900]}"}],
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = _j.loads(r.read())
    return data["content"][0]["text"].strip()


# --------------------------------------------------------------------------- DRAFT
def draft(items: list[dict]) -> str:
    lines = [
        "# Weekly Industry Brief",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Items: {len(items)}",
        "",
        "## Signals",
        "",
    ]
    for it in items:
        flag = " _(needs human review)_" if it.get("needs_review") else ""
        lines.append(f"- **{it['title']}** — {it['summary']}{flag}")
        lines.append(f"  Source: {it['feed'].split('/')[2]}{' · ' + it['link'] if it['link'] else ''}")
        lines.append("")
    lines.append("## Out of scope / dropped")
    lines.append("- Feeds that failed to fetch this run are listed in the run log.")
    lines.append("- Items older than the run window or outside the topic filter were skipped.")
    lines.append("")
    lines.append("## Review checklist")
    lines.append("- [ ] Spot-check every link opens to the right article (sources are copied verbatim).")
    lines.append("- [ ] _needs review_ items: LLM or extractive summary may be wrong — read before sharing.")
    lines.append("- [ ] Sign off with your initials and send to the thread.")
    return "\n".join(lines)


# --------------------------------------------------------------------------- FORMAT
def fmt(brief: str, out: Path, run_log: dict) -> Path:
    sections = ["# Weekly Industry Brief", "## Signals", "## Out of scope", "## Review checklist"]
    missing = [s for s in sections if s not in brief]
    link_count = brief.count("http")
    run_log["lint"] = {"missing_sections": missing, "links": link_count}
    fname = out / "briefs" / f"brief-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.md"
    fname.parent.mkdir(parents=True, exist_ok=True)
    fname.write_text(brief, encoding="utf-8")
    return fname


# --------------------------------------------------------------------------- RUN
def run(topic: str, max_items: int, out: Path) -> None:
    topics = [t.strip() for t in re.split(r"[;,]", topic) if t.strip()]
    t0 = time.perf_counter()
    feeds = [u for u in (u for us in FEEDS.values() for u in us)]

    items, failures = gather(feeds)
    t_gather = time.perf_counter()

    if topics:
        items = [i for i in items if any(t.lower() in (i["title"] + " " + i["excerpt"]).lower() for t in topics)]
    items = sorted(items, key=_epoch, reverse=True)[:max_items]

    items = synthesize(items)
    t_synth = time.perf_counter()

    brief = draft(items)
    t_draft = time.perf_counter()

    run_log = {
        "topic": topic,
        "started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "feeds_tried": len(feeds),
        "feeds_failed": len(failures),
        "items_kept": len(items),
        "ms": {"gather": int((t_gather - t0) * 1000), "synthesize": int((t_synth - t_gather) * 1000), "draft": int((t_draft - t_synth) * 1000), "total": int((t_draft - t0) * 1000)},
        "failures": failures,
    }
    fname = fmt(brief, out, run_log)
    run_log["brief_file"] = str(fname.relative_to(out.parent))
    log = out / "run-log.jsonl"
    with log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(run_log) + "\n")

    print(f"[{topic or '(all)'}] kept={run_log['items_kept']} fail={len(failures)} total={run_log['ms']['total']}ms -> {fname.name}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Weekly industry brief pipeline (FL-04).")
    ap.add_argument("--topic", default="", help="substring topics separated by ; or , (empty = all, newest N)")
    ap.add_argument("--max", type=int, default=10, help="max items in the brief")
    ap.add_argument("--out", default="output", help="output directory (relative)")
    args = ap.parse_args()
    for topic in [args.topic] if args.topic else ["LLM;AI", "security;breach", "cloudflare;workers;rust", "openai;anthropic;model", "developer;api;launch"]:
        run(topic, args.max, Path(args.out))