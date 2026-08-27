# Design Doc — CampaignBooster (one page)

## Problem
Small marketing teams (agencies, freelancers, SMBs) spend 3–6 hours hand-writing a
campaign plan: deciding channels, drafting per-channel briefs, listing every asset,
roughing a budget, and assembling a deliverable doc — often redoing it per client.

## 10x insight
One-line goal -> **complete, structured campaign package** (plan, briefs, asset
checklist, budget, guardrail, shareable report) in ~a minute, with every output
schema-validated and every decision explained. A person's hour becomes ~seconds.

## Solution overview
CampaignBooster runs a fixed, visible pipeline over the goal:
1. **Plan** — goal -> `CampaignPlan` (channels, audiences, objectives) via a pluggable
   generator (mock offline; LLM provider swappable).
2. **Guardrail** — validate the plan; reject with reasons instead of silently passing.
3. **Budget** — per-channel cost model -> projection in integer cents + USD.
4. **Checklist** — plan -> actionable asset checklist with ownership and status.
5. **Report** — compose everything into a Markdown/HTML deliverable.

## Program concepts (≥5) implemented
1. **Multi-stage pipeline orchestration** — stages run off-request in a background
   thread, with retries+backoff, live progress, and accumulated cost.
2. **Structured schema-validated output** — `CampaignPlan` (Pydantic) enforces every
   stage's result shape.
3. **Guardrail / validation with rejection + explanation** — an invalid/vague plan is
   flagged with reasons, not silently accepted.
4. **Cost & budget accounting** — integer-cents cost model per stage and per channel.
5. **Report / artifact generation** — a final shareable Markdown + HTML deliverable.
6. **Provider abstraction / pluggability** — generator + config via env; mock by default.

## Scope / non-goals
- Mock plan generator default; live LLM is an optional provider (TDY).
- No asset rendering, scheduling, or posting (those are other capstones).
- No persistence of runs beyond in-memory state (fine for a demo deliverable).

## Success metric
A 3-to-6-hour manual task completes in < 2s and yields validated, actionable output:
**"10x" = ~1000x faster to a first complete deliverable.**
