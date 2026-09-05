# FL-04 — Ship an Automation Workflow v2

Runnable **weekly industry brief** pipeline (GATHER → SYNTHESIZE → DRAFT → FORMAT) with five
real runs against live feeds on 2026-09-05 UTC. Requires Python 3.10+ and outbound HTTPS,
stdlib only.

- `weekly_brief.py` — the workflow; run with `python weekly_brief.py [--topic T] [--max N] [--out D]`.
- `walkthrough.md` — step diagram, every prompt/config, the five runs, honest time accounting
  (incl. setup cost and 6-run break-even), and named failure points + required human review.
- `output/briefs/` — five real brief files (`brief-*.md`), one per run/topic.
- `output/run-log.jsonl` — per-step timing, feed failures, and lint results for each run.