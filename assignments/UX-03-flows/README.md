# UX-03 — Users, jobs, flows (IA map + 3 flows)

## Collaborator
Sana — caregiver for her mother, works full-time, manages 2 specialists + medications.

## IA map (grouping logic)
```
CareMate
├─ Home (upcoming timeline, next visit, quick actions)
├─ Who am I caring for? (profiles)  ─┐ group: "People" — everything flows from the patient
├─ Book visit (specialty → date/time → confirm)
├─ Visits (upcoming / past, reschedule, cancel)
├─ Assistant (AI chat, confirmations, trust+governor patterns)
└─ Settings (clinics, notifications, hours log)
```
**Grouping logic:** group by *job* the caregiver performs (see next), not by provider — so
“Book”, “Visits”, and “Assistant” all operate on the currently selected patient profile.

## The 3 jobs + flows (decision points + unhappy paths)

### 1. Book a first visit
Start → pick patient → specialty → choose slot → **decision: is slot open?**
  - open → **confirm assistant** → success → timeline updated
  - taken → offer 2 alternatives
- **Unhappy path:** no slots that day → offer next available + “text me when open”.

### 2. Reschedule an existing visit
Start → Visits → choose visit → **decision: which day/time?** → **decision: what if new slot is unavailable?**
  - available → old slot held until new confirmed → done
- **Unhappy path:** the new date passes but nothing confirmed → keep old booking + warn (no lost slot).

### 3. Ask the assistant “what’s next?”
Start → Assistant → ask → **decision: does the model need a tool (reschedule)?**
  - yes → **confirmation governor** → runs → result card with source links
  - no → plain answer
- **Unhappy path:** tool fails → designed error + retry (never a crash).

## Deliverable check
- IA map covers every screen with grouping logic stated → tree above.
- All 3 flows include decision points and ≥1 unhappy path → ✓ per flow.
- A peer can follow each flow without explanation → the steps are linear and labeled.

## Repo links
- Prototype screens: `https://github.com/Eldasoky1/FlyRank-assignments/tree/master/assignments/UX-track-prototype`
- This file: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/UX-03-flows/README.md`