# FE-08 — Checkpoint 1 (errors, skeletons, empty states, sabotage test)

Built in the capstone app. This is Checkpoint 1 of the FE-11 production build.

## What was done
- **Mid-stream failure → designed error with retry**: `useStreamingChat.js` throws on
  `mid-stream`/`http-429`/`bad-json`/`empty` sabotage and the UI renders `role="alert"` with a
  Retry button that re-sends the last user message (`ChatWindow.jsx`).
- **Skeletons match real content layout**: the pending-state skeleton mirrors the assistant
  bubble geometry (title + body lines), so no CLS when content arrives.
- **Designed empty state, not an apology**: "No conversations yet — try asking about the capstone
  plan" with a clickable example (composer placeholder).
- **One automated sabotage test that runs on every commit**: `e2e/chat.spec.js` sets
  `window.__SABOTAGE = ['mid-stream']` and asserts the error UI + Retry render.

## Failure rehearsal order (reviewer script, rehearsed first)
kill network before send (`net-down`) → kill mid-stream (`mid-stream`) → return 429 (`http-429`)
→ malformed tool JSON (`bad-json`) → empty conversation on first run (site default).

## Deliverable check
| Criterion | Where |
| --- | --- |
| Mid-stream failure → designed error + working retry | `ChatWindow.jsx` + `useStreamingChat.js` |
| Skeletons match layout (no CLS) | `MessageList.jsx` |
| Empty state is designed onboarding | `MessageList.jsx` |
| Automated test for mid-stream failure path | `e2e/chat.spec.js` |

## Repo links
- Error UI: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/frontend-capstone/src/components/ChatWindow.jsx`
- Sabotage harness + e2e: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/frontend-capstone/e2e/chat.spec.js`