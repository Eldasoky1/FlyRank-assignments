# React-App-with-AI — build a similar React application independently using AI

Capstone (CUSTOM-MRC9R0VW). "Build a similar React application independently using AI as a
development assistant." I used the same assistant-driven loop I've trained across the FE track to
build **StreamChat**, a React 18 + Vite + Tailwind streaming AI chat with a tool-state machine.

## The completed application

- Repo: `frontend-capstone/`
- What it does: streaming AI chat (`/api/chat` SSE), a single `check_dates` tool with a
  four-state machine (`running / needs_input / result / error`), confirmation before tools run,
  designed error/retry, skeletons, an accessible playground (dialog/combobox/accordion), 15
  component tests + Playwright e2e, and a health-check page.
- Run: `node api/mock.js` then `npm run dev` (see `frontend-capstone/README.md`).

## The prompts used during development

Recorded prompts (first-principles versions; the full conversation is out of repo, these are the
exact seeds that produced the shipped code):

1. **Scaffold** — "Create a Vite + React 18 project at frontend-capstone named StreamChat. Use
   Tailwind 3 with semantic tokens ink/paper/accent/danger/ok and *-soft variants. Structure:
   src/components, src/hooks, src/test/setup.js (jest-dom + cleanup + reset window.__SABOTAGE)."
2. **Hook** — "Write useStreamingChat: consume /api/chat via response.body.getReader, accumulate
   parts.stream, model activeTool with states needs_input→running→result|error. Keep a
   streamAnswer ref to avoid hook ordering bugs. Support sabotage: net-down, mid-stream, http-429,
   bad-json, empty."
3. **Tool card** — "Extend ToolResultCard to a 4-state machine. Error state renders role=status,
   data-tool-state=error, a line with data-testid=tool-error, and Retry (→onConfirm) + Dismiss
   (→onCancel). Do not change other states."
4. **Message list** — "MessageList: designed empty state ('No conversations yet — try asking about
   the capstone plan'), skeletons matching bubble layout, aria-live polite streaming region.
   Guard scrollIntoView for jsdom."
5. **Tests** — "Write component tests querying by role and label, never by CSS class. Cover chat
   message renderer (all states), one validated form (composer), one tool-result component. ≥6."
6. **E2E** — "Playwright spec: primary flow ask→stream→assistant bubble; error path with
   window.__SABOTAGE=['mid-stream'] asserting designed error + Retry; empty state visible."

## How AI assisted (short explanation)

- **Speed**: full component tree, hook, and tests came from the prompts above; the diff-vs-blank
  cost was minutes, not days.
- **Where it failed / I corrected** (manual improvements, corrections, refactoring performed after
  reviewing AI-generated code):
  1. **Hook ordering bug**: initial `send` referenced `streamAnswer` before declaration → I refactored
     to safe `streamAnswerRef`, removing a stale-closure class of bug.
  2. **jsdom gaps**: `scrollIntoView` not implemented → guarded with `typeof === 'function'`.
  3. **Skeleton logic**: the first skeleton test passed empty messages and expected a pulse, but the
     empty *state* (not skeleton) is the correct design — I corrected the test to model the real flow,
     letting design intent drive the assertion instead of the AI's guess.
  4. **Fork-vs-extend**: round-one (FE-04) showed the AI forking `ToolResultCard` into a parallel
     component; I constrained it to extend the existing machine and validated with tests.

## Deliverable check

| The submission should include | Where |
| --- | --- |
| The completed application | `frontend-capstone/` |
| The prompts used during development | this document, "prompts" section |
| A short explanation of how AI assisted | this document, "how AI assisted" |
| Manual improvements/corrections/refactoring | the rotated-bullets above |

## Repo links
- App: `https://github.com/Eldasoky1/FlyRank-assignments/tree/master/frontend-capstone`
- This write-up: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/capstones/react-app-with-ai/README.md`