# Reusable report template

Fill the three placeholders and paste the whole block into any chat model.

```text
You are a concise engineering lead writing a <WHO> for <AUDIENCE>, who reviews many of
these each week, so it must be scan-able in 30 seconds and every number must match my
tracking data.

CONTEXT: I am <WHO_YOU_ARE>, and this week I worked on <PROJECTS>. What the audience needs
from me is <COACHING_SIGNAL_THEY_USE> (e.g. "to know what to coach me on").

Style target — imitate this rhythm exactly, evidence-first sentences, numbers before verbs,
no adjectives:
> "<ONE example paragraph from a previous good report>"

TASK: Write a report from the log below. Do this in three steps and show steps 1 and 2:
1. EXTRACT: list every number from the log with the sentence it came from; drop any number
   without a source sentence.
2. DRAFT: produce exactly four sections, in order, under 400 words total:
   - Summary: one headline sentence, max 30 words
   - Delivered: bullets, each starting with a verb and containing at least one number
   - Blocked: at most two lines, ending with a status word (resolved / waiting / escalating)
   - Next: exactly one priority for the following week
3. SELF-CHECK: verify order, word count, and that every number in the output exists in step
   1. Fix violations, then print the final report.

LOG:
<PASTE_YOUR_WEEK_LOG_HERE>
```

Why each block exists (so you can edit, not just use):
- **Role + audience** fixes tone and density (V1).
- **Context** tells the model what to optimize for: verification and scan-ability (V2).
- **Example** sets the mechanical style (V3).
- **Section contract** makes output structure reproducible, not vibes (V4).
- **Extract → Draft → Self-check** turns the accuracy rule into an enforced step and makes
  the audit trail visible to your reviewer (V5).