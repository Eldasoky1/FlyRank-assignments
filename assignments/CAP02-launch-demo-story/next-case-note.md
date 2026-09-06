# Capstone 2 — Send the Link: Launch, Demo & Story

## Brief (what this is about)

This capstone turns the class artifact of the internship (the personal site built in PF-04)
into a career platform by writing down exactly where the next case study goes, how to add one,
naming the next real piece of work, and keeping the build context cheap to reuse.

## 1. How to add the next case study (concrete steps)

Where it goes: the **Projects / case-study** section of the personal site
(`assignments/PF-04-personal-website/site/index.html`).

Steps:

1. Open `index.html` and duplicate the newest project card; change title, tag, description.
2. Add a short detail block under the card (one or two paragraphs).
3. Use the Week 2 **three-beat shape**: **problem** → **what I did** → **what came of it**.
4. Commit to `master` and redeploy using the Pages flow (blake3 hash → asset upload →
   production deployment).
5. Post the update and the live link once deployed.

The same note is pinned in `CAP01-impact-project/next-case-note.md`, so the process is shared
and never re-invented.

## 2. Next piece of work (named) + reminder (evidence)

Named next piece of work: a **case study for the LinkedIn Automation MCP Server**, written
in the three-beat shape:

- Problem: manual LinkedIn outreach is slow and un-personalized.
- What I did: built an MCP server (19 tools: connection requests, follow-ups, content
  posting; Python + FastAPI, wired into Claude flows).
- What came of it: a demoable agent tool that speeds up outreach and follow-ups.

Reminder set (evidence of the reminder):

- **Recurring calendar note:** "1st of every month at 18:00 — Add or refresh one case study
  on ahmed-eldasoky.pages.dev (three-beat shape)." Created as a repeating event starting
  **Sunday, 2026-09-27**.
- **One-off nudge:** a note on **2026-10-01** named "Draft LinkedIn-MCP case study" linking
  to the pinned note above.

## 3. Building context preserved

The Claude Project used to build the site (copy, design tokens, skills used for the PF-04
redesign) is kept up to date in Claude, so the next case study is a short conversation, not
a full rebuild.

## Pass / revise check

- [x] Concrete "how to add the next case" note, not a vague intention.
- [x] A specific next piece of work named, with a real reminder set.
- [x] The build context (Claude Project) is preserved for cheap future updates.