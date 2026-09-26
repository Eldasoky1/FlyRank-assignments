# UX-08 — Interactive prototype

The complete **Book a visit → confirm → success** flow works end-to-end in
`assignments/UX-track-prototype/index.html`.

## How it works
- Tab navigation (Home / Book / Assistant) — every screen reachable.
- Book flow: choose specialty → date → time → **Confirm booking** → jumps to Assistant where the
  change is pending confirmation → **Confirm change** saves it, showing the result state.
- Set “Anyone with the link” false here for repo-sharing; the Figma mirror is shared with
  “anyone with the link can view” so a reviewer outside the Figma team can open it.
- No dead ends: every decision has a visible outcome; the error state has Retry and Dismiss.

## Primary flow check
| Step | Screen | Outcome |
| --- | --- | --- |
| 1 | Home (upcoming) | context |
| 2 | Book a visit | form |
| 3 | Confirm booking | routes to Assistant confirm |
| 4 | Assistant confirm → Confirm change | success chip, timeline-style result |

## Deliverable check
- Primary flow completes start to finish without dead ends → verified in the prototype.
- Prototype link opens for someone outside your Figma team → Figma share setting: Anyone with the link can view (mirror). Repo-hosted prototype also viewable by link above.

## Repo links
- Prototype: `https://github.com/Eldasoky1/FlyRank-assignments/tree/master/assignments/UX-track-prototype`
- This file: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/UX-08-prototype/README.md`