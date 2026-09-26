# UX Capstone — Edge Cases: 10 nightmare scenarios, designed

**Assignment:** Take your high-fidelity screens, list 10 "nightmare" scenarios (API fails, search
returns nothing, etc.), and design the UI states for those edge cases (time-boxed to ~90 min).

## The 10 nightmare scenarios (CareMate)

| # | Nightmare | Designed state (in prototype: `assignments/UX-track-prototype/index.html`) |
| --- | --- | --- |
| 1 | API fails on load | Home shows designed error card with Retry (UX-06) |
| 2 | Search returns nothing | Empty state with a click-to-book example action |
| 3 | User types a 500-char name | Input `error` variant + inline message |
| 4 | Slot just taken between load and confirm | Taken-slot state with 2 alternatives; old slot held |
| 5 | Assistant tool feed unreachable | Tool error card with Retry + Dismiss (UX-07) |
| 6 | Reschedule deadline passes unconfirmed | Warn chip; old booking kept (no lost slot) |
| 7 | Empty upcoming visits | Designed onboarding empty state |
| 8 | No slots today (metadata-driven) | "Next available" + text-me-when-open |
| 9 | Network down mid-stream (AI reply) | Streaming cursor stops; error state with Retry (UX-07/UX-08 rehearsal) |
| 10 | Bad data from a tool (malformed payload) | Result card shows designed "couldn't read the data" fallback, not a crash |

## Rule applied
Every state must feel designed — text + tokens + action, not a bare error text or a crash. The
mandatory 6 (Empty, Loading Skeleton, Error, plus 3 more of these) are all present across the Home,
Book, and Assistant screens; see `UX-06-states/README.md` and `UX-07-ai-surface/README.md`.

## Deliverable check
- 10 nightmare scenarios listed → table above.
- UI states designed for the edge cases (a separate Edge Case page equivalent) → states 1–10 above, each realized in the prototype; bonus states for loading skeleton (Home/Book) and empty (Home/Assistant).

## Repo links
- Prototype (edge states): `https://github.com/Eldasoky1/FlyRank-assignments/tree/master/assignments/UX-track-prototype`
- States doc: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/UX-06-states/README.md`
- This file: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/capstones/ux-edge-cases/README.md`