# FE-10 — Lighthouse + accessibility pass

Performed on the capstone app.

## What was done
- **Lighthouse (mobile preset)** against the deployed production build (`npm run build` → static
  `dist/`; run targeted locally against `vite preview`). Baseline recorded and kept in the README
  perf note. Target: mobile performance + accessibility ≥90 (80 absolute min per rubric).
  - Total JS gz ≈ 49 kB, single chunk, no third-party runtime → perf headroom.
- **WAVE** on key pages: landmarks, single h1, labelled controls, no color-only state (tool states
  use text + border + `*-soft` fills, not colour alone).
- **Keyboard-only pass** through the primary flow (chat + tool + health tab): Tab order, labelled
  textarea, Enter to send, Confirm/Retry/Dismiss + Escape path on the tool card, dialog Escape.

## Growth to 90+ a11y that mattered
- Every interactive control has an accessible name (`aria-label`, real `<label>`, or button text).
- `role="log"` + `aria-live="polite"` for the streaming region; `role="alert"` for errors.
- Contrast: `ink` (#0f172a) on `paper` (#f8fafc) = AA; semantic filled states tested in WAVE.
- Reduced motion: tool-state transitions keep a 200ms crossfade only (no large animation loops);
  streaming uses text, not motion.

## Deliverable check
| Criterion | Where |
| --- | --- |
| Lighthouse mobile perf + a11y ≥90 | recorded baseline in `frontend-capstone/README.md` "Performance note" |
| WAVE run on key pages | a11y section above |
| Keyboard-only pass incl. chat | dialog Escape + tool card + composer (above) |

## Repo links
- App README (perf note + a11y design): `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/frontend-capstone/README.md`
- Source: `https://github.com/Eldasoky1/FlyRank-assignments/tree/master/frontend-capstone/src`