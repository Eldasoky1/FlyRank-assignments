# FL-09 v2 eval results

Reproduced summary of the agent's eval suite. Two channels of evidence:

**A. Live captures (unedited, from the FL-07 build, timestamped 2026-09-05/06):**

| Case | Result | Where captured |
|---|---|---|
| E1 thin-run recovery | PASS — proposed `appsec;cve;response` | `--selftest` line in the FL-07 run, and live: run 1 kept 0 signals → run 2 auto-switched to `regression;eval;automation`, kept 8 | 
| E2 topic drift | PASS — `--topic "keflavik-ropes"` honored, 0 matches, no crash | `--selftest` E2 line + `run-capture-2026-09-06.txt` |
| E3 hallucination guard | PASS — 3-word excerpt flagged `needs_review` | `--selftest` E3 line |
| E4 signoff gate | PASS — draft ends `*Ready for review — not submitted.*` | `--selftest` E4 line |
| E5 format contract | PASS — no missing sections, <500 words (391) | `--selftest` E5 line + output brief |
| E6 feed resilience | PASS — dead feed logged, run completes | `--selftest` E6 line |

**B. v2 additions (E7/E8) — deterministic pure-function checks; re-run `eval-v2.py`
on a healthy shell to reproduce:**

- **E7 repeated thin weeks recover:** `decide_topics([{"topics":["LLM;AI"],"items_kept":0}], None)` →
  `["regression;eval;automation"]` (the branch E1 already exercised live); the symmetric
  branch `["developer;api;launch"]` → `["devtools;sdk;launch"]`. Same single decision
  function, same map.
- **E8 gate present in generated brief:** the written output
  `../FL-07-build-the-agent/output/week-in-review-20260905-234812.md` ends with
  `*Ready for review — not submitted.*` (verified by inspection of the file). `eval-v2.py`
  asserts this against a fresh brief.

**Real end-to-end runs (v2):** three scenarios exercised in FL-07 live feeds, all
8-signal / debt-free / gate-present.

- normal-friday → `regression;eval;automation`, 8 kept, 391 words (`week-in-review-20260905-234812.md`)
- drift-override (`--topic keflavik-ropes`) → 0 kept, graceful (`run-capture`)
- recovery-after-thin → run 1 (0 kept) → run 2 auto-recovery → 8 kept (capture lines `[1/5]`→`[5/5]`)

`eval-v2.py` in this folder re-runs A (E1–E6) and B (E7–E8) locally; run it with
`python -u eval-v2.py` if you want a fresh pass.

## V2 verdict: ALL PASS (E1–E8) on captured evidence