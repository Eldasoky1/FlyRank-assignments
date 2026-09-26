# UX-11 — Case study writeup

## CareMate — an AI booking assistant for caregivers
_A telehealth companion that books, reschedules and confirms medical visits in under 90 seconds._

## The arc (research → tested prototype)

### 1. Research
Caregivers juggle bookings across clinics, portals and phone lines. Desktop interviews
(UX-02) surfaced 5 findings — the biggest: **users fear losing a slot** and **want confirmation
before the assistant saves a change**.

### 2. IA & flows (UX-03)
Grouping by *job* (Book / Visits / Assistant) around a selected patient profile. Three flows with
decision points and unhappy paths: book-first-visit, reschedule (old slot held until confirmed),
and ask-the-assistant.

### 3. Wireframes (UX-04)
Built the booking screen twice: a Figma AI draft vs hand-built. The diff was specific — the AI
produced a flat form with no failure states or trust copy; the hand-built version had hierarchy,
held-slot logic and error/alternative states.

### 4. Design tokens & components (UX-05)
Semantic tokens as CSS variables (no hard-coded hex in components), Button/field/tab/bubble/chip/
tool-card built on them.

### 5. States (UX-06) & AI surface (UX-07)
Empty/error/loading states on 3+ screens. The assistant ships 5 patterns incl. a **governor**
(cap: 1 change per request) and a **trust builder** (citations on every change).

### 6. Tested prototype (UX-08 → UX-09)
End-to-end book→confirm flow with no dead ends. Three usability sessions found exactly the
anxieties research predicted; we shipped 3 fixes (visible before/after): reschedule on the visit
card, confirm-before-save, designed empty Home.

### 7. Accessibility & polish (UX-10)
AA contrast, keyboard, labels, ARIA live region, reduced-motion-safe.

## What changed because of the test
Trust copy + confirm-before-save (findings 4) were already designed; testing added the 3 usability
fixes above. Success metric held: median booking task under 90 seconds, ask-again rate low.

## Deliverable check
- Tells the full arc with real artifacts at each step → sections 1–7, each pointing to its folder.
- Includes usability results and what changed because of them → section 6–7.
- Scannable in under 5 min; a non-designer understands it → yes (section-per-phase above).

## Repo links
- Prototype: `https://github.com/Eldasoky1/FlyRank-assignments/tree/master/assignments/UX-track-prototype`
- This file: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/UX-11-case-study/README.md`