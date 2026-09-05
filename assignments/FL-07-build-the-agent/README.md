# FL-07 — Build the Agent (MVP)

The FL-06 spec, built: a **weekly review scout** that merges my weekly log and live industry
feeds into one mentor-review-ready brief, selects this week's topics from how last week's
runs went, and **stops** at a signoff gate instead of submitting anything.

## Files

- `week_in_review.py` — the agent (epoch-free, stdlib + optional Anthropic call). Reuses the
  FL-04 `weekly_brief` module for GATHER/SYNTHESIZE so only the new decision loop + gate are
  new code.
- `run-capture-2026-09-06.txt` — raw, unedited capture of a successful end-to-end run
  (command → 5 steps → brief → gate). Shows thin-run recovery firing for real: run 1 kept 0
  signals, so run 2 auto-restarted with `regression;eval;automation` and kept 8.
- `output/week-in-review-20260905-234812.md` — the produced brief (Summary / Blocked /
  Signals / Next, 391 words, gate line).
- `output/agent-run.jsonl` — every run, with topics, items kept, feed failures, and lint.
- `weekly-log-2026-09-04.md` — the week's log the agent reads (real, this week's FL-04/05/06).
- `build-log.md` — honest build log: the 0-signal filter bug, the prefix bug, and the
  documented deviations (rule-based topic branch when no API key; interactive pre-gather
  cut; tightened LLM budget).

## For the reviewer

- Data connections used (≥1 required): live HTTPS RSS (external service), filesystem read of
  run history, filesystem write of the brief.
- Eval cases E1–E6 from the spec are enforced, not decorative: `python week_in_review.py
  --selftest` prints all six with assertions and exits non-zero on any failure.

## Run it

```
python week_in_review.py --selftest
python week_in_review.py --log weekly-log-2026-09-04.md            # normal Friday run
python week_in_review.py --log weekly-log-2026-09-04.md --topic "agents;mcp"   # drift override
```