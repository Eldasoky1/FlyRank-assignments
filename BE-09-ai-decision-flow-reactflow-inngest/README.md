# BE-09 · AI Decision Flow (React Flow + Inngest)

A visual **AI decision flow** for routing support tickets. It pairs two
essential tools of the modern AI backend stack:

- **React Flow (`@xyflow/react`)** — renders the branching decision graph and
  highlights the path the AI actually takes, live.
- **Inngest** — turns that same decision into a **durable, step-based
  workflow** (`routeTicket`), where every unit of work is checkpointed and
  resumes cleanly if the process dies.

**Stack:** ⚛️ React 18 + TypeScript + Vite · 🧭 React Flow · 🔁 Inngest · ✅ Vitest.

---

## The problem

A support ticket arrives. An AI must decide which team/branch it belongs to
(`billing`, `technical`, `account`, `sales`, or `other`), then run that
branch's actions in order. We want to **see** that decision happen, and we
want the backend to treat each step as recoverable — not as one big, opaque,
retry-the-whole-thing call.

## The design

```
               ┌────────────────────────────────────────────┐
   ticket ───▶ │  React Flow (UI)                           │
               │  shows: start ▸ AI intent ▸ branches ▸ end │
               └───────────────┬────────────────────────────┘
                               │  same step sequence
                               ▼
               ┌────────────────────────────────────────────┐
               │  Inngest `routeTicket` (backend, durable)  │
               │  step: detect-intent                       │
               │  step: expand-branch                       │
               │  step: execute:<action> (×N, idempotent)   │
               └────────────────────────────────────────────┘
```

The **single source of truth is `src/domain/branchRouter.ts`** — the AI
classifier + branch definitions. Both the React Flow runner and the Inngest
function call the same functions, so the UI and the backend can never drift
apart.

### React Flow (`src/components/FlowCanvas.tsx`, `src/flow/graph.ts`)

- A hand-laid-out graph: **Start → AI intent → 5 branch nodes → End**.
- As the flow runs, `applyRunState` paints the winning branch
  (`stroke: #7c3aed`, width 3) and **animates** the active edges.
- Custom node components (`start / intent / branch / end`) keep the canvas
  readable.

### Inngest (`inngest/routeTicket.ts`)

```ts
export const routeTicket = inngest.createFunction(
  { id: "route-ticket", name: "Route a support ticket to a branch" },
  { event: "ticket/new" },
  async ({ event, step }) => {
    const intent = await step.run("detect-intent", () => classifyMessage(message));
    const branch = await step.run("expand-branch", () => branchSteps(intent.category));
    for (const action of branch) {
      await step.run(`execute:${action.label}`, () => ({ step: action.label, ok: true }));
    }
    return { message, intent, executed };
  },
);
```

Each `step.run` is **durable**: Inngest checkpoints it. On a crash it resumes
from the last finished step instead of re-running the AI decision (a key
property of AI-in-the-loop workflows).

### Offline runner (`src/flow/runFlow.ts`)

`safe/sane`: the UI and tests call `runDecisionFlow()`, which executes the
**exact same step sequence** without needing an Inngest server/cloud, emitting
`onIntent` + `onStep` events for the canvas to animate.

---

## AI decision branch map

| Branch | Signals | Actions |
|--------|---------|---------|
| `billing` | charge, refund, invoice, payment… | Look up subscription → Compute refund → Issue refund |
| `technical` | error, crash, bug, 500, freeze… | Gather logs → Run diagnostics → Propose fix |
| `account` | password, forgot, locked out, 2fa… | Verify identity → Reset access → Notify user |
| `sales` | plan, upgrade, pricing, trial… | Recommend plan → Build offer → Send offer |
| `other` | (no signal) | Assign human agent → Escalate |

Confidence rises with the number of matched intent keywords and is clamped to
`0.98`. The router is deterministic and fully unit-tested; in production the
single `classifyMessage` function is swapped for a real LLM call — the rest of
the flow is untouched.

---

## Run it

```bash
cd BE-09-ai-decision-flow-reactflow-inngest
npm install

# 1) React app (the visual decision flow)
npm run dev            # http://localhost:5173

# 2) Inngest dev server (serves the durable workflow, in another terminal)
npm run inngest:dev    # http://localhost:8288
# then send a test event:
#   curl -X POST http://localhost:8288/e/ticket/new \
#     -H 'Content-Type: application/json' \
#     -d '{"data":{"message":"I was charged twice, refund please"}}'

# 3) Production build
npm run build
```

## Tests

```bash
npm test
```

**13 Vitest tests** — all offline (the Inngest function is imported but never
hits a server). Coverage:

- AI router picks the right branch for billing / technical / account / sales /
  other messages,
- confidence stays in `0..0.98` and rises with more keyword hits,
- every branch exposes **ordered, non-empty** steps, and the billing branch
  has exactly the expected refund steps in order,
- the offline runner executes branch steps in order to `done`, fires
  `onIntent` with the right category, and emits each `onStep` transition,
- the `routeTicket` Inngest workflow object is exported under the
  `ticket/new` trigger.

---

## Files

```
BE-09/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── inngest/
│   ├── client.ts          # Inngest client (id: "ticket-router")
│   └── routeTicket.ts     # the durable step function + trigger event
├── src/
│   ├── App.tsx            # canvas + control panel + run log
│   ├── main.tsx
│   ├── styles.css
│   ├── domain/
│   │   ├── types.ts       # Category / Intent / FlowStep
│   │   └── branchRouter.ts# THE classifier + branch map (single source of truth)
│   ├── flow/
│   │   ├── graph.ts       # React Flow node/edge layout + path highlighting
│   │   └── runFlow.ts     # offline runner mirroring the Inngest steps
│   └── components/
│       └── FlowCanvas.tsx # React Flow canvas + custom nodes
└── tests/
    ├── branchRouter.test.ts
    └── runFlow.test.ts
```
