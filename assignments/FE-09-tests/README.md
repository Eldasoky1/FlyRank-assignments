# FE-09 — Component + e2e tests

Built in the capstone app.

## What was done
- **15 component tests** (≥6 required), querying by role and label, never by test-id/CSS class for
  the brittle ones — renaming a CSS class cannot break them:
  - `ChatComposer.test.jsx` (label `Message the assistant`, Send button role) — 3
  - `ToolResultCard.test.jsx` (role=status, states) — 4
  - `MessageList.test.jsx` (log/skeleton/empty/bubbles) — 4
  - `HealthCheck.test.jsx` (loading/ok/error) — 3
  - `App.test.jsx` (shell) — 1
  High-risk UI covered: chat message renderer, one validated form (composer), one tool-result
  component (ToolResultCard) — exactly the rubric's three targets.
- **One Playwright e2e** walking the primary flow (`e2e/chat.spec.js`): ask → streams → assistant
  bubble; plus error-path and empty-state scenarios.

## Deliverable check
| Criterion | Where |
| --- | --- |
| ≥6 meaningful component tests; class renames safe | `npm run test` → all 15 pass; queries by role/label |
| One Playwright e2e walking primary flow | `e2e/chat.spec.js` |

## Repo links
- Tests: `https://github.com/Eldasoky1/FlyRank-assignments/tree/master/frontend-capstone/src/components`
- E2E: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/frontend-capstone/e2e/chat.spec.js`
- Test config: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/frontend-capstone/vite.config.js`