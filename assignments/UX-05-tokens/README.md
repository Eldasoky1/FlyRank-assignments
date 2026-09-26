# UX-05 — Design system foundations: tokens and components

## Tokens (semantic, applied via variables — never hard-coded hex)
Declared in the prototype as CSS custom properties under `:root`, semantic names only:

| Token | Value | Where used |
| --- | --- | --- |
| `--color-bg` / `--color-surface` / `--color-surface-2` | #fbfcfe / #ffffff / #f1f5f9 | app shell, cards |
| `--color-text` / `--color-text-mute` | #0f172a / #64748b | type |
| `--color-primary` / `-soft` / `-fg` | #2563eb / #eff6ff / #ffffff | buttons, active tab |
| `--color-danger` / `-soft` | #dc2626 / #fef2f2 | error states |
| `--color-ok` / `-soft` | #16a34a / #f0fdf4 | success chips |
| `--color-warn` | #d97706 | held-slot notice |
| `--space-1..6`, `--radius-1`, `--radius-2`, `--radius-pill` | spacing/radii scale | all layout |
| `--shadow-1`, `--font-sans`, `--font-mono` | elevation, type | depth, code |

All components reference `var(...)` tokens only — no literal hex outside `:root`.

## Components (from the token set)
- Button (primary / secondary), chip/status, card, field+input+select, tab bar, bubble (user/assistant), tool card, skeleton line.

## Deliverable check
- Tokens use semantic names and are applied via variables, not hard-coded hex → confirmed; components only use `var(--…)`.

## Repo links
- Token block: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/UX-track-prototype/index.html`
- This file: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/UX-05-tokens/README.md`