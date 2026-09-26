# StreamChat — Frontend AI Engineering Capstone

Queue of what my reviewer asked for, satisfied here:

- FE-05: Tailwind + design tokens (a11y-friend semantic palette), deploy pipeline and health-check page.
- FE-06: streaming AI chat (SSE mock + streaming renderer).
- FE-07: user-interaction tool with a four-state machine (running / needs-input / result / error) + designed transitions.
- FE-08: Checkpoint 1 — mid-stream failure with designed error + Retry, matching skeletons, a real empty state, one automated sabotage test.
- FE-09: 15 component tests querying by role/label + Playwright e2e walking the primary flow.
- FE-10: accessibility-driven component structure (ARIA roles, labelled inputs, keyboard-first) with Lighthouse budget in the perf note.
- FE-11: production-ready README (below) and deploy notes.

## What it does

A small AI chat with a single "check dates" tool. The model asks before running the tool
(`needs_input`), shows running, streams output tokens that accumulate as a buffer (no broken
markdown mid-stream), renders a result card, and — when the tool fails — a designed error state
with Retry instead of a crash. The empty state is designed onboarding, not an apology.

## Quick start

```bash
npm install
# terminal 1: mock backend (SSE + health) on :5199
node api/mock.js
# terminal 2: vite dev on :5198 (proxies /api -> :5199)
npm run dev
# open http://localhost:5198
```

## Scripts

| Script | Purpose |
| --- | --- |
| `npm run test` | Vitest + Testing Library component tests (15) |
| `npm run test:watch` | watch mode |
| `npm run e2e` | Playwright e2e (primary + error + empty flows) |
| `npm run build` | production build to `dist/` |
| `npm run preview` | serve the production build |

## Env vars

| Var | Used by | Required |
| --- | --- | --- |
| `VITE_CHAT_ENDPOINT` | chat fetch URL (defaults to `/api/chat`) | no |
| `VITE_HEALTH_ENDPOINT` | health-check fetch URL (defaults to `/api/health`) | no |

## Architecture

```
frontend-capstone/
├─ src/
│  ├─ App.jsx                  # shell + tabs
│  ├─ index.css                # Tailwind base + design tokens
│  ├─ components/
│  │  ├─ ChatWindow.jsx        # wires hook → parts/status → UI
│  │  ├─ ChatComposer.jsx      # labelled textarea + send (a11y labels)
│  │  ├─ MessageList.jsx       # bubbles + streaming region + skeleton
│  │  ├─ MessageBubble.jsx     # user vs assistant rendering
│  │  ├─ ToolResultCard.jsx    # 4-state tool UI + Confirm/Retry/Cancel
│  │  └─ HealthCheck.jsx       # /api/health page
│  ├─ hooks/useStreamingChat.js# streaming fetch + tool state machine
│  └─ test/setup.js            # jest-dom + cleanup + sabotage reset
├─ api/mock.js                 # SSE streaming mock + /api/health + /api/chat
├─ e2e/chat.spec.js            # Playwright primary/error/empty flows
└─ vite.config.js              # port 5198 + /api proxy + vitest config
```

## Streaming model

`/api/chat` returns `text/event-stream`; the hook reads with `getReader()`, decodes incrementally,
and appends to `parts.stream`. Markdown is *buffered whole-part* (we only render the accumulating
plain-text stream; a dedicated `react-markdown` render can be added per part — the buffer is
kept intact so no half-fenced code block ever renders). Skeletons match the real bubble layout
to avoid CLS.

## Tool state machine

`state ∈ { running, needs_input, result, error }`, drawn before styling:

```
user typed tool-ish intent
        │
        ▼
  needs_input ──Confirm──▶ running ──ok──▶ result
        │                    │
     Cancel                  └─fail──▶ error ──Retry──▶ running
```

Each state answers a different user question: what is it doing? should it run? what came back?
what went wrong? Transitions are a 200ms crossfade (CSS `transition`), never a layout jump.

## Failure rehearsal (FE-08)

Set `window.__SABOTAGE = ['net-down' | 'mid-stream' | 'http-429' | 'bad-json' | 'empty']`
before sending a message to force each failure. `e2e/chat.spec.js` covers mid-stream.

## Performance note (FE-10)

Total JS gz ~49 kB (single Vite chunk, stripped of dev deps). Target Lighthouse mobile ≥90 perf &
a11y: semantic landmarks, labelled form controls, no CLS-prone skeletons, `aria-live="polite"`
streaming region. Nothing external; mock API is local.

## How AI tools built this

Claude Code scaffolded the component tree and tests, wrote the streaming hook and the sabotage
rehearsal harness, and generated this README. I reviewed the state machine, fixed hook-ordering
bugs, adjusted jsdom gaps (scrollIntoView), and validated the build/test/e2e loop manually.

## Deploy note

`npm run build` produces static `dist/`. Host anywhere (Vercel/Netlify/Cloudflare Pages); for a
portable fully-static preview run `npm run preview` after `node api/mock.js`.