# AI Fluency — Week 1 · Portfolio sitemap + pressure test

**Deliverable:** the first prompt pressure-tested the map, and I noted at least one thing I'll change.

## The sitemap (sketch)

```
ahmed-eldasoky.pages.dev
├─ /             Home — hero: proof statement + one action
│                "Clear the noise: one page that makes you believe, then ask."
├─ /#work        Work / case studies (3 cards → newest first)
├─ /#about       Short about: who + why
├─ /cv.html      CV (print-friendly; linked from Home + LinkedIn)
└─ footer        Contact (email/linkedin), booking (calendly: pending)
```
Rules applied: **one person, one action** (land → believe the proof → contact). I resisted adding
pages "just because" — no blog, no separate "projects", no tools page.

## The Claude Project (built for this)
- **Name:** `fl-cap` (personal-portfolio build; Claude Project `f4d401b2-…`)
- **Custom instructions (pasted proof statement):**
  > You are my tutor and design critic for building my portfolio. My proof statement: _"I build
  > reliable backend systems and AI integrations that remove manual work, proven by my FlyRank
  > internship capstones which passed review, not by a certificate."_ Act as a demanding tutor:
  > ask sharp questions, pressure-test my decisions, and never flatter.

## The pressure-test prompt (real, saved verbatim)
> "Tutor mode. Here is my sitemap (home, #work, #about, cv, footer-contact; one action = contact).
> My proof statement is pasted in your instructions. Pressure-test the sitemap against that one
> action and that claim. Where would a skeptical visitor get lost, and what's the single weakest
> link? Give me the top 3 risks and exactly what to change."

## The AI's answer (saved)
1. **About-before-belief:** `#about` before `#work` makes the visitor read biography before proof → reorder: **work first**.
2. **No visible proof on the fold:** the claim mentions capstones, but there's no case-study link on the fold → put one card + link in the hero.
3. **Contact is a dead-end without a next step:** "email me" is friction → add a specific "book a 15-min intro call" CTA.

## What I'll change (chosen)
I'll **reorder to work-first** and add a single hero case-study link — the highest-leverage fix so a
visitor sees proof before biography, and the contact action has a concrete next step.

## Deliverable check
- First prompt pressure-tested the map → yes (3 risks above).
- Noted at least one thing you'll change → reorder to work-first + hero case-study link.

## Repo link
`https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/AI-fluency-sitemap/README.md`