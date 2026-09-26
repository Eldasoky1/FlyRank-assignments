# FE-07 — User-interaction tool + four-state machine

Built in the capstone app.

## What was done
- **User-interaction tool**: `check_dates` — the model asks before running (`needs_input` state
  with Confirm & run / Cancel), fulfilling "confirmation before an action runs".
- **Four tool states machine** (`running / needs_input / result / error`), drawn before styling:
  ```
  needs_input ─Confirm─▶ running ─ok─▶ result
       │                   │
     Cancel              └─fail─▶ error ─Retry─▶ running
  ```
  Each state answers a different question (what is it doing? should it run? what came back?
  what went wrong?). See `ToolResultCard.jsx` + `useStreamingChat.js`.
- **Designed error state**: the component only makes sense when the tool succeeds → the error
  state is designed first, with Retry + Dismiss; reviewers can trigger failure on purpose via
  `window.__SABOTAGE`.
- **Transitions**: 200ms crossfade on state change (CSS transition on the card), no layout jump.

## Deliverable check
| Criterion | Where |
| --- | --- |
| User-interaction tool (confirmation) | `needs_input` → Confirm & run |
| Four states with distinct treatments | `ToolResultCard.jsx` (`data-tool-state`) |
| Failed tool shows designed error, not a crash | `error` state + Retry/Dismiss |
| State machine documented | README "Tool state machine" |

## Repo links
- Component: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/frontend-capstone/src/components/ToolResultCard.jsx`
- Hook logic: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/frontend-capstone/src/hooks/useStreamingChat.js`