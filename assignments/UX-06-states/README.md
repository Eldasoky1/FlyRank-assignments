# UX-06 — Build (core): empty, error, loading states

Three screens in the prototype (`assignments/UX-track-prototype/index.html`) each ship designed
non-happy states — not bolted-on.

## 1. Home — Upcoming visits
- **Loading:** skeleton lines sized to the real layout (70% / 45% widths) inside the card — no layout shift.
- **Empty:** “No upcoming visits” copy is designed as onboarding — plus a primary “Book a visit” action.

## 2. Book a visit — slot selection
- **Error:** taken-slot state offers two concrete alternatives and explains the hold logic, so failure is a decision, not a dead end.
- **Loading:** fields + confirm button render instantly; only the slot list is skeletoned.

## 3. Assistant — tool run
- **Loading:** streaming bubble with animated cursor (progress disclosure).
- **Error:** designed error card (“We couldn’t reach the schedule feed”) with Retry + Dismiss — never a toast-only “error”.
- **Success:** confirmation chip + result detail with full text.

| Screen | Empty | Error | Loading |
| --- | --- | --- | --- |
| Home | ✓ | — | ✓ |
| Book | — | ✓ (taken slot) | ✓ |
| Assistant | (welcome bubble) | ✓ (feed error + retry) | ✓ (streaming) |

## Deliverable check
- Empty, error, and loading states exist for 3+ screens and feel designed → matrix above; all styled with semantic tokens.

## Repo links
- Prototype: `https://github.com/Eldasoky1/FlyRank-assignments/tree/master/assignments/UX-track-prototype`
- This file: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/UX-06-states/README.md`