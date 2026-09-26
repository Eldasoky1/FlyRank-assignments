# AI Fluency — Week 6 · Explain in plain words (backend + data flow)

**Deliverable:** a short plain-words explainer: what a backend is, what my feature does, and how the
data flows — in my own words, correct and showing I understand the data flow.

## What a backend is (my words)
A backend is the part of a system that runs *away from the screen*: it stores data, applies rules/
permissions, and does the real computation. The frontend (your browser) just asks it questions and
paints the answers.

## The feature (FlyRank capstone — social studio scheduler)
My **Social Studio** capstone lets a brand type one caption and schedule it for publishing; the
backend posts it **once** (never twice), signs webhook callbacks, and reports each job's status.

## How the data flows (in my words)
```
You (browser)                            backend                          DB / external
  typed caption
      │  POST /posts                        │
      ▼                                    │
  "please schedule this" ──────────────────▶  validate + save job  ──▶ tasks.db (publish_jobs)
      │                                    │  (status: pending)
      │                                    ▼
      │   later, a scheduled publish run    │
      │        pulls due jobs ────────────▶  publish to platform ──▶ external API
      │                                    │  status: done/delivered
      │                                    ▼
      ◀── GET /posts/{id} ─────────────────▶  returns status to the screen
```

- **In:** my frontend posts a payload → backend writes a pending row (only destination is storage).
- **Through:** a durable scheduler later reads *due* jobs and publishes exactly once (idempotency
  via content hash + a `publish_jobs` unique key).
- **Out:** signed webhook callbacks confirm delivery; the UI polls the job id to show a designed
  "delivered" state.

I understand the data flow because the whole lifecycle (write → schedule → publish exactly once →
callback → status) is implemented, tested (20/20), and running in the repo.

## Deliverable check
- Explainer is correct, in my own words, and shows understanding of data flow → the three sections + diagram.

## Repo links
- Capstone: `https://github.com/Eldasoky1/FlyRank-assignments/tree/master/flyrank-capstone-socialstudio`
- This file: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/AI-fluency-backend-explainer/README.md`