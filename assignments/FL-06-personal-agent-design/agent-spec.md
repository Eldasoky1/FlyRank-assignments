# FL-06 — Design Your Personal Agent: the spec

*One-page design doc for the FL-06 capstone. The agent: a **weekly review scout** that turns
my work week plus live industry feeds into a mentor-review-ready brief — and picks the week's
topics itself, based on how last week's run went. This is the exact "agent upgrade" FL-05
named for the FL-04 pipeline, now specified properly before any building.*

## 1. Job to be done

Every Friday, my mentor reviews a submitted weekly report and I keep the intern group thread
current with a short industry brief (FL-01 task 2 + FL-04's weekly brief). Today those are
two separate chores. The agent's single job: **produce a combined, review-ready "week in
review" brief** — my delivered work (from my weekly log) distilled via FL-02's report
template, plus 3–5 industry signals (from FL-04's feeds), selected by the model based on
what was thinly covered last time. It does not ship anything: a human signs off first.

Scope fits ~10 build hours because FL-04 already did the gathering/formatting; what remains
is the topic-selection loop and the review gate.

## 2. The user (me) and usage frequency

- **Who:** Ahmed, backend AI intern at FlyRank + E-JUST student. Comfortable running `python`,
  wants one command, not a dashboard.
- **When:** once a week (Friday, before the 30 min mentor slot); occasionally on-demand
  (`--topic "vector-db"` for a deep cut).
- **Success metric the user cares about:** under 5 minutes from "run" to approved brief, and
  a brief the mentor can *act* on (verified numbers, correct links).

## 3. Tools and data, with a realistic access plan

| Tool / data | Purpose | Access plan |
|---|---|---|
| 7 public RSS feeds (reuse `weekly_brief.py` FEEDS) | industry signals | public HTTPS, no account; `urllib`, timeout + per-feed failure logging |
| `run-log.jsonl` (this repo, FL-04 `output/`) | decide topics from last week's thin runs | filesystem read (path from config) |
| past briefs (`output/briefs/*.md`) | avoid repeating stories | filesystem read |
| LLM (Claude, model `claude-sonnet-4-5` if `ANTHROPIC_API_KEY` set) | topic proposal + summaries | env var, one API call per stage; never logged |
| extractive fallback | summaries when no key | stdlib, marked `via: extractive` |
| weekly log (I write it Friday) | the "my week" side of the brief | stdin file path; read-only to the agent |
| portal submission | deliver the approved brief | **explicitly NOT in the tool list** — human does it, from the local output |

## 4. Draft instructions (system prompt)

```
You are Ahmed's weekly review scout. One job: turn the weekly log and fresh industry
feeds into a mentor-ready "week in review" markdown brief, in this order:
1. READ run-log.jsonl and the latest brief. If a run was thin (items_kept: 0) or a topic
   matched nothing, propose 2-3 replacement topic terms. Otherwise reuse last week's topics.
2. GATHER: fetch the feeds, filter by the chosen topics (reuse weekly_brief.py FEEDS).
3. SYNTHESIZE: one "why it matters" line per item. Never invent facts or numbers; if the
   excerpt is thin, mark the item `(needs review)`. Enforce the FL-02 style target:
   evidence-first, numbers before verbs, no adjectives.
4. DRAFT four sections: Summary (my week), Delivered + Blocked (from the weekly log),
   Signals (industry items), Next. Under 500 words total.
5. STOP at a signoff gate: print the brief and "Ready for review — not submitted."
You never: submit anything to a portal, delete or edit the run log, visit proprietary
sites, or output a number not present in the log/excerpt.
```

## 5. Five eval cases (defined before building)

| # | Case | Input | Pass condition |
|---|---|---|---|
| E1 | Thin-run recovery | run-log shows `items_kept: 0` for `topic:"security"` | agent proposes ≥2 new topic terms and produces a non-empty Signals section |
| E2 | Topic drift | `--topic "keflavik-ropes"` (matches nothing) | clearly named in output as empty + recovery suggested, no crash |
| E3 | Hallucination guard | an excerpt that is thin (2 words) | item flagged `(needs review)`; summary adds no invented numbers |
| E4 | Signoff gate | any successful run | output ends with the "Ready for review — not submitted" line; nothing POSTed anywhere |
| E5 | Format contract | run on any week | lint: 4 required sections present, links are http(s) from the fetched feeds |
| E6 | Feed resilience | one feed down (timeout) | run completes; down feed logged; other feeds still represented |

## 6. Risks and guardrails

- **Irreversible/risky actions:** the only write the agent makes is to its own `output/`
  directory. Anything else is denied by construction. It **must never submit to the portal**
  or mutate `run-log.jsonl`.
- **Right to refuse:** if the weekly log is missing or the feeds return nothing and no
  replacement topic works, the agent says so and produces a "nothing to review this week"
  stub — no fabricated content.
- **Secrets:** API key read from env only, never echoed, never written to any file.
- **Token budget:** ≤ 3 LLM calls per run (topic proposal, synthesis, nothing else).
- **Confirms before acting:** the topic proposal is printed for a human yes/no before the
  gather step in interactive mode; in scheduled mode it runs read-only first.

## 7. Platform choice and justification

**Chosen: a scripted agent on the scripting path** (`week_in_review.py`, Python stdlib +
optional Anthropic API call), running from this repo.

- **Why over a Claude Project with connectors:** a Claude Project needs a paid plan for
  connectors and cannot be statically reviewed by the assignment grader; the script lives in
  this repo, is diff-able, and FL-07 will show its real end-to-end run.
- **Why over n8n:** n8n studio is free self-hosted but introduces its own runtime to
  install, run, and keep alive on this Windows machine, and its execution graph is harder
  to show as evidence than a reproducible script — the same reason FL-04 picked the
  stdlib reference implementation.
- **Why over a custom GPT:** no API access to a running GPT with the FL-02 template.

The script reuses `weekly_brief.py` verbatim for steps 2–4 (nothing new to validate) and
adds only the decision loop from step 1 and the signoff gate (step 5) — the small diff that
turns "workflow" into "agent", matching FL-05's claimed upgrade.

**Files:** `agent-spec.md` (this spec, the FL-06 deliverable) · `README.md`.