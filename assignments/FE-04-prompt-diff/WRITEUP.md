# FE-04 — Same feature, two prompts: the prompt-diff drill

Pick one small capstone-relevant feature and build it twice: once with a deliberately lazy prompt,
once with a precise prompt (file refs, constraints, example behavior, verification step).

## The feature

**ToolResultCard error state** — the four-state tool UI in `frontend-capstone/src/components/ToolResultCard.jsx`.
Small, well-scoped, part of the capstone's central interaction.

## Round one — vague (one sentence, no context)

> "Add an error state to the tool card."

**Prompt honestly lazy?** Yes — no file references, no constraints, no behavior spec, no tests.

What AI did: invented its own card layout with inline `style`, no ARIA, no `role=status`,
no Retry affordance, no keyboard support. It didn't look at the existing `ToolResultCard`
(which already had a `running|needs_input|result` state machine), so it produced a *parallel*
component that would never mount.

## Round two — precise (explore → plan → code → verify)

> Repo: `frontend-capstone`. File: `src/components/ToolResultCard.jsx` (read first).
> Add a fourth state `error` to the existing state machine. Keep the existing card markup and
> Tailwind tokens (`danger`, `danger-soft`). The error state must: render `role="status"` with
> `data-tool-state="error"`, show a `data-testid="tool-error"` line, and provide a Retry button
> that calls `onConfirm` and Dismiss that calls `onCancel`. Do not change the other three states.
> Verification: add/update `ToolResultCard.test.jsx` (query by role/testid, never class) asserting
> the error state renders the designed error, Retry, and Dismiss; then run `npm run test`.

What AI did: read the file, extended the existing machine, reused tokens, added exactly the
specified states + buttons, wrote the test, ran the suite. Passed first run. Because round one's
lazy output was *discarded*, the diff taught the floor-vs-ceiling gap: **no context ⇒ a parallel
component; context ⇒ a state added to the existing machine the way the reviewer expects.**

## Route-cause note

The lazy prompt actually looked *decent* on the surface (a red card), which is exactly the
failure the brief warns about — without the constraint "extend the existing state machine, do not
re-create the card," the AI couldn't know to integrate rather than duplicate. That constraint,
plus a verification step, is the whole difference.

## My reusable prompt preamble (used from here on)

> **Context**: project `frontend-capstone`, React 18 + Tailwind 3 with semantic tokens
> (`ink/paper/accent/danger/ok` + `*-soft`), tests with Testing Library + Vitest, query by
> role/label/testid.
> **Rules**: read the relevant file before editing; extend existing structures, never fork them;
> keep ARIA roles and keyboard behavior intact; ship a verification step (test or build) with
> every change; never invent files that shouldn't exist.

## Deliverable check

| Criterion | Where |
| --- | --- |
| Round-one one-sentence prompt | above |
| Round-two precise prompt | above |
| Write-up names ≥1 AI mistake I caught | the parallel-component mistake (twice) |
| 3 rules → reusable preamble | above; applied to capstone build & tests |