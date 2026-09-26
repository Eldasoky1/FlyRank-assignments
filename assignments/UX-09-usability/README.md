# UX-09 — Usability test and iterate

## Method
Moderated remote, 3 participants (caregivers of family members), 20 min. Tasks written as
scenarios, not clicks.

## Tasks
- T1 — “You need to book a Cardiology visit for your mother sometime this week.” (scenario, not “click Book”)
- T2 — “You booked Thursday 11:00 but the clinic just called with a conflict — switch it to Wednesday afternoon.”
- T3 — “Find out what happens next; how do you know it worked?”

## Findings
1. **T2 stumble:** participants looked on Home for reschedule instead of Dashboard → moving the entry into the visit card fixed it.
2. **Confirmation anxiety:** users were unsure whether the change was *saved* until the success chip appeared → added inline confirm copy + result state.
3. **Empty-home confusion:** with no visits, Home looked broken → designed empty state with a book action (UX-06).

## Top 3 fixes shipped (before/after)
| # | Before | After |
| --- | --- | --- |
| 1 | Reschedule buried in Dashboard | “Reschedule” button directly on the Next appointment card (prototype Home) |
| 2 | “Confirm booking” silently saved | Assistant confirm step + explicit result copy before save |
| 3 | Empty Home showed nothing | Designed empty state + primary book CTA |

All three are visible in `assignments/UX-track-prototype/index.html`.

## Deliverable check
- Tasks are scenarios (“you want to…”) → T1–T3 phrasing above.
- Top 3 fixes shipped to the prototype with visible before/after → table above; changes live in the prototype.

## Repo links
- Prototype: `https://github.com/Eldasoky1/FlyRank-assignments/tree/master/assignments/UX-track-prototype`
- This file: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/UX-09-usability/README.md`