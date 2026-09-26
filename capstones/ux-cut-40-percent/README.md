# UX Capstone — Cut your UI by 40% (wireframes + changelog)

**Assignment:** Take the capstone product, cut screen/UI elements (or flow features) by 40%,
show what you cut vs kept in a wireframe/flow, and document the change in a changelog.

## What I cut (from the original CareMate idea set)
The v0 scope imagined an admin dashboard, a provider directory, in-app messaging, a pharmacy
partner feed, and a multi-patient family hub. Cut:

| Removed | Why |
| --- | --- |
| Admin dashboard | separate audience (clinic staff not caregiver) |
| Provider directory | discovery is not the pain — switching systems is |
| In-app messaging | text confirmations cover the need (research finding 3) |
| Pharmacy partner feed | out of v1 scope; no signal it’s wanted |
| Multi-patient family hub → single active profile | reduces IA + permission complexity |

**Kept (the most viable):** Home timeline, Book visit, Visits (reschedule/cancel), Assistant
(confirm+governor), Settings. That’s 5 surfaces vs the 10 original → **~50% cut**.

## Before/after wireframes
The kept surfaces are wireframed (low-fi) and realized in the interactive prototype:
`assignments/UX-track-prototype/index.html`. The cut items simply don’t exist — the IA map
(`UX-03-flows/README.md`) shows the reduced tree.

## Changelog
```
Changelog — CareMate v0.2 scope cut
- REMOVED: Admin dashboard (audience mismatch)
- REMOVED: Provider directory (not the pain)
- REMOVED: In-app messaging (text reminders suffice)
- REMOVED: Pharmacy partner feed (out of v1)
- REMOVED: Family hub (active-profile model instead)
- KEPT: Home, Book, Visits, Assistant, Settings
- ADDED: confirmation-before-save (research finding 4)
- NOTE: 10 surfaces → 5 (−50%)
```

## Deliverable check
- Low-fi cut wireframe or flow → reduced IA + kept-surface wireframes (see UX-03) and prototype.
- Changelog documents what you cut and kept → above.

## Repo links
- IA/flow (reduced): `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/UX-03-flows/README.md`
- Prototype (kept surfaces): `https://github.com/Eldasoky1/FlyRank-assignments/tree/master/assignments/UX-track-prototype`
- This file: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/capstones/ux-cut-40-percent/README.md`