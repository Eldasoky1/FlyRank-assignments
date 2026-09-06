# Narration script (demo video) — "Week in Review" agent

*For the speaker. The on-screen replay is the real, unedited end-to-end run from
`run-capture-2026-09-06.txt` (roughly 0:00–0:45), then the frame holds so you can explain
what each step does and why (0:45–3:30), ending **on the guardrail card** (3:30+).*

## 0:00–0:45 · The run, live

"Okay — this is the agent doing its one job, end to end, no hand-editing. I type one
command: `week_in_review.py --log weekly-log-2026-09-04.md`.

Step one, it reads its own run history. Notice interesting: last Friday's run was thin —
zero signals for the `LLM;AI` bucket. The agent doesn't retry the dead topic. Its solve is
built into the decision step: it proposes `regression;eval;automation` as the week's topics.
That's the exact 'make topics model-driven' upgrade I named in FL-05, now implemented.

Step two, it fetches live feeds — seven public RSS sources, 1,300 raw items, zero failures.
Step three, it filters on those topics and synthesizes one-line 'why it matters' notes.
Step four, it drafts the four sections the mentor reads: Summary, Blocked, Signals, Next.
Step five — the part that makes this an agent and not a script — it lints the output and
signs off: 'Ready for review — not submitted.' Look at the JSON it prints: eight items,
under 500 words, all sections present."

## 0:45–3:30 · Design decisions (while the frame holds)

"Three decisions worth calling out.

One, the job boundary. This agent's scope is a *brief*, not a submission pipeline. Every
tool is read-only on anything outside its own output folder, and the sign-off gate is the
only interactive moment, other than topic overrides. That's the FL-06 scope discipline: one
job done well.

Two, what makes it 'agentic' vs the FL-04 workflow. FL-04 took topics as a parameter. This
agent owns the topic decision by reading `agent-run.jsonl` — last week's metrics change this
week's behavior. Success triggers a deterministic, auditable recovery instead of guessing.

Three, evals came first. The FL-06 spec defined six cases before any code. E1 fires in
this very capture. On senior-review weeks the thing to watch is E3 — the hallucination
guard — any thin excerpt is flagged `(needs review)` rather than filled in. My E1–E6
selftest exits non-zero on any regression, and v2 adds E7/E8."

## 3:30–end · The guardrail, on camera

"Here is the guardrail, live: this run ends on a line that says the brief is *not*
submitted. The agent holds no credentials to the portal, opens no connection to it, and
cannot touch my run log or my notes. All it can do is write one markdown file into its own
output directory. A human reviews, spot-checks flagged items, and posts the link.

And the limitation I'll own on camera: with no API key set, summaries are extractive, and
an Hacker-News item occasionally surfaces a mechanical line — 'points, comments' — instead
of a takeaway. That's exactly what the `_ (needs review)_` flag is for. It's in the
README's limitations list, and it's the honest reason the gate exists in the first place."

*End on the red guardrail card.*