# UX-04 — Wireframes: AI draft vs hand-built

Same screen both ways: the **Book a visit** screen (specialty → date/time → confirm).

## AI-generated draft (Figma AI prompt: “booking form”)
- Stacked generic inputs, all equal weight — no sense of which field matters.
- No empty/selected state; no “hold my slot” microcopy; no error handling shown.
- Buttons labelled “Submit” — ambiguous.
- **Specific observation:** AI produced a *form*, not the *flow* (no decision points, no alternatives when a slot is taken).

## Hand-built version (with research applied)
- Specialty first (drives slots), date/time grouped, then a **confirmation zone** (“We’ll hold Cardiology 11:00 AM until you confirm.”).
- Includes taken-slot state with 2 alternatives; empty state on Home (“No upcoming visits”).
- Explicit trust copy + governor (limit 1 change per request).

## Comparison (specific, not “AI is faster”)
| Dimension | AI draft | Hand-built |
| --- | --- | --- |
| Hierarchy | flat form | task-driven order (specialty → slot → confirm) |
| Failure states | none | taken slot → alternatives; held-slot logic |
| Trust copy | none | “held until you confirm” + governor note |
| Screen coverage | 1 | Home empty state + booking + confirmation + error |

**Conclusion:** AI is a great *draft engine*; the value is the local copy/clinic-slot logic the
draft can’t infer. Best workflow = AI draft → human passes it through the UX-03 flow checklist.

## Deliverable check
- Comparison includes specific, non-generic observations → the table above (hierarchy, failure states, trust copy, coverage).

## Repo links
- Prototype implementing the hand-built decisions: `https://github.com/Eldasoky1/FlyRank-assignments/tree/master/assignments/UX-track-prototype`
- This file: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/UX-04-wireframes/README.md`