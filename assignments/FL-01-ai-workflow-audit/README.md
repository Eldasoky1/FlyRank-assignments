# FL-01 — AI Workflow Audit and Tool Setup

Author: Ahmed Eldasoky
Track: AI Fluency (Foundation) · Backend AI Engineering — July 2026

## 1. Weekly workflow audit

I tracked one realistic working week (study + internship + side projects) and listed the
recurring tasks I actually do. Each task is classified into one of four buckets:

| Bucket | Meaning |
|---|---|
| **Just me** | I should keep doing this myself; AI adds noise or risk |
| **Delegate to AI with review** | AI drafts/produces, I verify before it leaves my hands |
| **Collaborate with AI** | Back-and-forth: AI suggests, I decide, AI refines |
| **Fully automate** | Hands-off pipeline; a human checks outputs only occasionally |

Classification rule I used: **"Whoever reads a bad output suffers?"** — if the failure is
embarrassing/externally visible (a message to a client, a posted report), I keep a human in
the loop. If the failure is cheap and reversible, it can be fully automated.

| # | Task (real, recurring) | Where it happens | Classification | Rationale (one line) |
|---|---|---|---|---|
| 1 | Review PRs in the widget-platform repo | GitHub | Just me | I am accountable for merge quality; AI summaries miss subtle integration risk. |
| 2 | Write the weekly intern progress report for my FlyRank mentor | Notion → email | Delegate to AI with review | A first draft saves 20 minutes; I still check every claim against the week's log. |
| 3 | Attend E-JUST lecture on distributed systems and compress it into study notes | Notion | Delegate to AI with review | Notes must be source-grounded; I verify each claim against the recording. |
| 4 | Prepare questions for the weekly 1:1 with my mentor | empty notebook | Collaborate with AI | AI probing helps surface blind spots, but the final list has to sound like me. |
| 5 | Build and maintain the FlyRank MCP server (flyrank-mcp repo) | Local dev | Just me | My capstone-adjacent project; architecture decisions are mine. |
| 6 | Debug failing CI pipeline for social-studio repo | GitHub Actions | Collaborate with AI | AI reads the log faster; I own which fix gets merged. |
| 7 | Draft LinkedIn posts about what I am learning | LinkedIn | Delegate to AI with review | Drafts in my tone in 5 minutes; I rewrite anything that sounds generic. |
| 8 | Update my CV after each milestone | Google Docs | Delegate to AI with review | Structure suggestions help; quantified achievements must be exact. |
| 9 | Track internship progress against capstone milestones | spreadsheet | Just me | It is my accountability map; automation would hide drift. |
| 10 | Read engineering newsletters and filter what deserves my time | RSS reader | Fully automate | Cheap and reversible: a misfilter costs 30 seconds, not a missed deadline. |
| 11 | Summarize the weekly industry brief into a 300-word digest | my notes → Discord | Delegate to AI with review | Speed matters more than recall; I spot-check facts before sharing. |
| 12 | Meal planning and workout logging | app | Fully automate | Template from last week is good enough; human only corrects exceptions. |
| 13 | Transcribe and action-item my mentor call recordings | Otter → Notion | Delegate to AI with review | Fast extraction, but action items must match what we actually agreed. |
| 14 | Refactor utility functions and write their unit tests | Local dev | Collaborate with AI | AI proposes the refactor and tests; I run the suite and review diffs. |

### "Just me" honesty check

The brief asks that at least two tasks be honestly marked **"just me"** with a reason:

- **Task 1 (PR reviews):** I tried letting an AI draft review comments. The comments were
  plausible but missed a data-loss edge case in a migration. Merge reviews are the last
  quality gate — I keep them human.
- **Task 5 (MCP server design):** This is my project and I need to *understand* every line.
  The fluency skill is deciding *who* should do the work; for architecture of my own
  project, that person is me.

## 2. Toolkit setup

| Tool | Account | Status | Evidence |
|---|---|---|---|
| Claude | Personal account | Configured | `claude-project-instructions.md` + screenshot of the project (see `evidence/`) |
| ChatGPT | Personal account | Available | Used in FL-02 cross-model run |
| Anthropic Academy (Anthropic Skilljar) | Enrolled with same email | Enrolled | Enrolled in *AI Fluency: Framework & Foundations*, first module completed |

## 3. Three target tasks reused in FL-02 → FL-04

Picked from the audit. "Done well" is defined before starting, so FL-02 (prompting) and
FL-04 (automation) have a measurable bar.

1. **Weekly industry brief** (task 11) — gather the week's AI/backend engineering news into
   a 300-word digest.
   - **Done well:** produced in under 15 minutes; 5+ named sources; no factual errors when
     spot-checked; can be read in one minute.
2. **Source-grounded study notes** (task 3) — turn a lecture into structured, cited notes.
   - **Done well:** every claim traces to a timestamp/slide; notes reviewable in a single
     pass; flashcard-ready (question plus answer).
3. **Draft, critique, revise** (task 2) — turn my weekly log into a first draft of the
   intern progress report, critique it, then revise.
   - **Done well:** mentor-facing draft under 400 words; my reviewer edits less than 20% of
     the produced text; every number matches the week's log.

## 4. Evidence

- `claude-project-instructions.md` — the custom instructions used for my Claude Project
  (who I am, tone, goals).
- `evidence/` — instructions for adding the screenshot of the configured Claude Project and
  the Academy enrollment confirmation.