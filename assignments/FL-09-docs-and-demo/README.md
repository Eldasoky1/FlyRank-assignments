# Week in Review — personal AI agent (weekly review scout)

Fl-07 agent, documented per the FL-09 brief: what it does and for whom · stranger-proof
setup · usage · architecture · v2 eval results · limitations.

## What it does and for whom

**For:** me (an AI-engineering intern) every Friday before my 30-minute mentor slot — and
for anyone who inherits the repo.

**One job:** merge my weekly work log with the day's freshest AI/security industry feeds
into a single **mentor-ready "week in review" brief**. The agent itself decides this week's
topics by reading how last week's runs went, so a dead topic (zero matching news) is
automatically swapped for a recovery term — no config to touch. It finishes by printing a
signoff gate and **never submits anything itself**; a human clicks "send".

Why the scope was cut this small (FL-06 spec): one job done well in ~10 build hours beats a
broad assistant that does nothing end to end.

## Stranger-proof setup

1. Clone and place the repo next to the FL-04 pipeline (the agent imports
   `assignments/FL-04-automation-workflow/weekly_brief.py` for fetching + summarising, so
   that folder must sit beside it):
   ```
   git clone https://github.com/Eldasoky1/FlyRank-assignments
   ```
2. Python 3.10+ (stdlib only). No `pip install` needed for the rules branch.
3. *(Optional)* export `ANTHROPIC_API_KEY` to enable the model-written one-line summaries
   and the model-proposed topic branch. Without it the agent runs the auditable
   rule-based branch instead — same eval cases pass.
4. Put your weekly log somewhere (any markdown with lines starting
   `Delivered:` / `Blocked:` / `Next:`), then run it.

## Usage

```
python assignments/FL-07-build-the-agent/week_in_review.py --selftest          # E1-E6, exit non-zero on failure
python assignments/FL-07-build-the-agent/week_in_review.py \
    --log my-week-2026-09-04.md --out assignments/FL-07-build-the-agent/output  # Friday run
python ... --topic "agents;mcp"                                                  # force this week's topics
```

Output goes to `--out/week-in-review-<timestamp>.md`; every run is appended to
`--out/agent-run.jsonl` with topics, items kept, feed failures, and lint results — which is
the data the agent uses to notice thin weeks next time.

## Architecture

```mermaid
flowchart LR
    A[weekly log .md] -->|read| D
    H[agent-run.jsonl] -->|read history| D
    F[[7 RSS feeds]] -->|HTTPS| G
    D{decide topic}\n read history\n + override + LLM? -->|terms| G[gather]
    G -->|raw items| L{filter + synthesize}
    L -->|signals| S[draft 4 sections]
    S -->|brief| V{lint + gate}
    V -->|write| O[(output/ brief + jsonl)]
    V -->|stop| P[human signoff, then send]
    style D fill:#ffe08a
    style V fill:#f9b4b4
```

Two decision points, both human-friendly: the **topic step** (yellow) decides *what* the
week is about and can recover from thin history; the **gate** (red) refuses to ship. The
gather/synthesize/draft legs are the FL-04 pipeline reused verbatim — the agent is the small
delta that adds the two decisions.

## v2 eval results

Run `eval-v2.py` in this folder to reproduce (appends E7/E8 to the FL-06 E1–E6 suite and
runs three timed end-to-end runs). Latest results — **E1–E8 all pass**; the three real
end-to-end runs are in `../FL-07-build-the-agent/output/`:
`eval-results-v2.md` in this folder. Highlights: thin-week recovery fires automatically
(0-signal run 1 → auto topic swap → 8 signals run 2, seen on camera in the demo), the gate
line is asserted present in every written file, and # guardrail that is exercised on camera
is *nothing ships without a human*.

## Limitations (honest list)

- **Weekly log parsing is regex-level.** Anything not phrased `Delivered:/Blocked:/Next:`
  is dropped silently. Fix with a richer parser or structured notes in v3.
- **Summaries can be thin.** With no `ANTHROPIC_API_KEY`, the extractive summariser
  sometimes grabs an HN-mechanics line (`Points: 1 # Comments: 0`) instead of a
  one-sentence take. That is why the `_ (needs review)_` flag exists — read flagged items.
- **No calendar/portal integration.** The gate is a printed line; the *send* is a human
  pasting a link into the portal. Deliberate (see guardrails), but slower than a full
  auto-file.
- **Substring topic matching.** `regression;eval;automation` matches "regression",
  "eval", etc. anywhere in title or excerpt — can pull near-misses. Exact/embedding matching
  is a v3 upgrade.
- **Single-user, single-machine.** No auth, no shared state; the run log is a local file.
- **Feed dependence.** Two feeds in the FL-04 set were already dead when audited
  (`blog.cloudflare.com/atom.xml`, `anthropic.com/news/rss.xml`); healthy ones carry the
  run. Feed downtime degrades signals, never crashes the agent.

## Links back to the track

FL-01 audited the manual weekly brief (task 2) · FL-02 gave the drafting prompt style used
here · FL-04 shipped the gather→synthesize→draft→format workflow · FL-05 named the
"make topics model-driven" agent upgrade · FL-06 specced *this* job with eval cases ·
FL-07 built it · this folder documents and demos it.