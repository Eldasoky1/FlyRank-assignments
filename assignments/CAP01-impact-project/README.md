# Capstone 1 — General AI Fluency · Impact Project

**Author:** Ahmed Eldasoky
**Track:** AI Fluency (Foundation) · July 2026 cohort
**Deliverable:** A documented "keep the portfolio alive" habit for the personal career platform at https://ahmed-eldasoky.pages.dev — with a concrete process for adding the next case study, a named next piece of work, and a reminder that ensures it actually happens.

## What this is about

Impact projects stop proving anything the moment they stall. This capstone is the habit setter that keeps the portfolio alive: I wrote down exactly how a second (and third) case study gets added to the personal site built in PF-04, named the next real piece of work, and set a concrete reminder to do it — so the process is never re-invented and the portfolio keeps growing.

## 1. How to add the next case study (concrete steps)

Where it goes: the **Projects / case-study** section of the personal site (`assignments/PF-04-personal-website/site/index.html`), which already renders project cards with a hover-glow design.

Steps to add one:

1. Open `index.html`, duplicate the newest project card markup, and change the title, tag, and description for the new case.
2. Put a short detail block right below the card (one or two paragraphs).
3. Follow the Week 2 **three-beat shape**: **problem** → **what I did** → **what came of it**.
4. Commit to `master` and redeploy: `blake3` hash the updated file, push through the Pages asset upload, and create a production deployment (same flow used for the PF-04 relaunch).
5. Post a "New case study" line (project updates) once it is live.

The exact same note is mirrored in `CAP02-launch-demo-story/next-case-note.md`, so the process is shared and never re-invented.

## 2. Next piece of work (named) + reminder (evidence)

Named next piece of work: a **case study for the LinkedIn Automation MCP Server** (one of my OpenAI Agents SDK / MCP projects — 19 tools for connection requests, follow-ups, and content posting, built with Python + FastAPI and wired into Claude desktop flows).

- **Problem:** manual LinkedIn outreach is slow and un-personalized.
- **What I did:** built an MCP server exposing automation tools an agent can call.
- **What came of it:** a working demoable agent tool that speeds up outreach and follow-ups.

Reminder set (evidence of the reminder):

- **Recurring calendar note:** "1st of every month at 18:00 — Add or refresh one case study on ahmed-eldasoky.pages.dev (three-beat shape)." Created as a repeating event starting **Sunday, 2026-09-27**.
- **One-off nudge:** a note on **2026-10-01** named "Draft LinkedIn-MCP case study" linking to the pinned note above.

## 3. Building context preserved

The Claude Project used to build the site (site copy, design tokens, skills: PF-04 redesign, banner/CP, design system) is kept in Claude and updated after each deploy, so the next case study is a short conversation instead of a rebuild.

## Pass / revise check

- [x] Concrete "how to add the next case" note, not a vague intention.
- [x] A specific next piece of work named, with a real reminder set.
- [x] The build context (Claude Project) is preserved for cheap future updates.
