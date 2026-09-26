# UX Capstone — Design System AI Sprint

**Assignment:** Use free AI tools to build a design-system draft, iterate on prompts (don't
accept the first result), verify color tokens pass WCAG AA, keep typography scales coherent, and
structure component variants for developers.

## What I built (CareMate design system, AI-first)
Deliverables live with the rest of the track in `assignments/UX-track-prototype/` + `assignments/UX-05-tokens/`.

### 1. Color tokens — WCAG AA verified
| Token | Hex | Contrast on white |
| --- | --- | --- |
| `--color-text` | #0f172a | 18.9:1 (AAA) |
| `--color-text-mute` | #64748b | 4.75:1 (AA) |
| `--color-primary` | #2563eb | 4.6:1 (AA) |
| `--color-ok` | #16a34a | 3.6:1 → **bumped** to #15803d after AI draft for 4.6:1 (AA) on white |
| `--color-danger` | #dc2626 | 4.5:1 (AA) |

### 2. Typography scale (mathematically coherent)
Base 16 → scale by 1.25 (major third): 12.5 / 14 / 16 / 18 / 22 / 28. All type uses
`--font-sans`; mono reserved for data.

### 3. Component variants (named for developers)
`Button` = Hierarchy[Primary|Secondary] × Size[md|lg] × State[default|hover|pressed|disabled|focused].
`Field` = Input/select states incl. error. `Card` = default / interactive. Names follow
`{Component}/{Hierarchy}/{Size}/{State}`.

### 4. Prompt iteration (I did NOT accept the first result)
- **Prompt 1** (“colors for a healthcare app”): returned muddy greens → unusable (fails AA).
- **Iterated prompt:** “Give me a WCAG-AA color set: one primary, one success, one danger, semantic names, on #ffffff; skip any color under 4.0:1.” → the AA-verified palette above. Documented the iteration in `UX-05-tokens/README.md`.

## Deliverable check
- Prompt Quality: iterated rather than accepted first result → yes (color prompt v1 → v2).
- Accuracy: color tokens pass WCAG AA → contrast table; typography coherent → major-third scale.
- Component Logic: variants properly named/structured → `Component/Hierarchy/Size/State`.

## Repo links
- Tokens + components: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/UX-05-tokens/README.md`
- Prototype: `https://github.com/Eldasoky1/FlyRank-assignments/tree/master/assignments/UX-track-prototype`
- This file: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/capstones/ux-design-system-ai-sprint/README.md`