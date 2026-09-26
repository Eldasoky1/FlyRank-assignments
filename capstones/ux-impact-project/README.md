# UX/UI Design · Impact Project — CareMate

_A single structured summary of the 8-week UX journey. Data-light, artifact-heavy — what I built,
how I used AI, and where to find everything. Short, honest, show the work._

---

## 1. Project snapshot

**Focus area:** UX/UI Design for a telehealth booking assistant — **CareMate** — for unpaid
caregivers who book appointments for family members across clinics, portals, and phone lines.

**Problem:** coordination, not discovery. Users book across 2–3 systems and fear losing a slot.

**Design target:** get a visit booked or rescheduled in under **90 seconds** with no phone call,
with confirmation before the assistant saves anything.

**3 key outcomes**
1. **Confirmation governess** — the assistant asks before saving every change (limit: 1 visit per
   request), directly addressing the "did it stick?" anxiety from research.
2. **Held-slot rescheduling** — the old slot is kept until the new one is confirmed, so users never
   lose coverage while switching.
3. **Designed failure/empty/loading states** on 3+ screens — every edge a reviewer can trigger is a
   state, not a crash (10-nightmare edge-case pass).

---

## 2. Week-by-week journey map

| Week | Deliverable | AI tools used |
| --- | --- | --- |
| W1 | Pitch + research synthesis (UX-01, UX-02) | Claude (synthesis, critique), Anthropic Academy Claude 101 |
| W2 | IA map + 3 flows with decision points & unhappy paths (UX-03) | Claude (critique of tree) |
| W3 | Wireframes — AI draft vs hand-built comparison (UX-04) | Figma AI (auto-draft), Claude (diff critique) |
| W4 | Design tokens + components (UX-05); states on 3 screens (UX-06) | Figma AI naming; DeepSeek (color/type scales) |
| W5 | AI surface: governor, trust, tool status, failure states (UX-07); interactive prototype (UX-08) | Claude (component logic) |
| W6 | Usability test + top-3 fixes (UX-09); accessibility & polish (UX-10); hours log (UX-12) | — |
| W7 | Case study (UX-11) + capstones: component matrix, edge cases, personas, AI design sprint, 40% cut, Figma org | DeepSeek/Claude (personas, matrices, transcripts) |

---

## 3. AI integration log

**Top 3 time-saving prompts**
1. *Persona + transcript seeding:* "Generate an 8-message interview with Sana about rescheduling;
   include a moment where she fears losing a slot." → usable persona transcripts in one shot
   (`capstones/ux-personas-transcripts`).
2. *WCAG-AA color prompt:* "Give me a WCAG-AA color set: primary/success/danger on #ffffff, semantic
   names, skip anything under 4.0:1." → the AA-verified token palette (iteration 2), fixing the
   muddy first attempt (`capstones/ux-design-system-ai-sprint`).
3. *Variant matrix prompt:* "List every Button/Hierarchy/Size/State combination, tab-separated." →
   the 30-cell Button matrix in one pass (`capstones/ux-component-matrix`).

**Failed-prompt lesson (1)**
My first design-system prompt ("colors for a healthcare app") returned **muddy greens that fail
AA**. The fix was forcing the *constraint* (contrast ≥ 4.0:1, white bg, semantic names) into the
prompt — teaching me that AI drafts are good, but *constraints, not vibes*, are what make them
usable. That lesson became the reusable "rules before output" pattern used in every later prompt.

---

## 4. Key artifact snapshots

| Artifact | Where to see it |
| --- | --- |
| Research synthesis (1 page) | `assignments/UX-02-research/README.md` |
| IA map / flows | `assignments/UX-03-flows/README.md` |
| Wireframes comparison | `assignments/UX-04-wireframes/README.md` |
| Tokens / components | `assignments/UX-05-tokens/README.md` + prototype CSS `:root` |
| Hi-fi prototype (interactive) | `assignments/UX-track-prototype/index.html` |
| Testing (before/after) | `assignments/UX-09-usability/README.md` |
| Accessibility pass | `assignments/UX-10-accessibility/README.md` |
| Case study | `assignments/UX-11-case-study/README.md` |

Screenshot of the prototype's Home/Book/Assistant tabs is rendered live by opening
`index.html` — every state (empty, error, loading, tool confirm, success) is in one file.

---

## 5. Tangible assets shipped (view-only links)

| Asset | Direct link |
| --- | --- |
| CareMate interactive prototype | https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/UX-track-prototype/index.html |
| Full UX track (12 assignments) | https://github.com/Eldasoky1/FlyRank-assignments/tree/master/assignments |
| UX capstones (6) | https://github.com/Eldasoky1/FlyRank-assignments/tree/master/capstones |
| Repo root | https://github.com/Eldasoky1/FlyRank-assignments |

All Figma-equivalent files (pages: Research / IA & Flows / Wireframes / Tokens / Components /
States / Prototype / Handoff) are organized under the area/status/owner convention documented in
`capstones/ux-figma-organization`.

---

## 6. Reflection

**Top 3 learnings**
1. **The empty/error/loading state is the product.** Six edge states are worth more than one happy
   path; every reviewer trigger point is a chance to build trust.
2. **AI is a draft engine, not a decision-maker.** The booking screen came back from Figma AI as a
   flat form; the *local* clinic-slot and trust logic is what made it a real flow.
3. **Constraints before vibes.** Iterating a prompt from "nice colors" to "AA ≥4.0:1 on white,
   semantic names" turned a muddy palette into a shipped token set.

**One major challenge overcome**
The research finding — users **trust** the assistant only if it confirms before saving — forced a
real architecture decision: a confirmation **governor** (limit 1 visit change per request) plus
held-slot-on-reschedule. Implementing both in a nested flow (do it, don't lose the old booking)
was the hardest 2 days of the build; usability testing (UX-09) confirmed it was the right bet.

---

*Deliverable for the UX/UI Design · Impact Project capstone (`ux-cap`). Artifact-heavy, ~3 pages,
everything above links to a real file.*