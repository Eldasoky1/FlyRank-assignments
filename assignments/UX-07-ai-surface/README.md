# UX-07 — Designing the AI surface: chat, agents, and trust

Patterns implemented in the prototype Assistant tab (`assignments/UX-track-prototype/index.html`).

## 4+ named patterns (2 are mandatory categories below)
1. **Confirmation governor** — the assistant asks before saving a reschedule; capped at **1 visit change per request** (a governor: bounds the agent’s blast radius).
2. **Trust builder (citations)** — every tool result shows what changed and the source (“Cardiology → Dermatology, Thu 11:00 AM”) so users can verify rather than trust blindly.
3. **Tool status / progressive disclosure** — a dedicated card shows pending → running → result, instead of a free-form bubble.
4. **Failure and uncertainty as a designed state** — connection failure renders a real error card with Retry, not a toast saying “error”.
5. **Streaming affordance** — animated cursor so users know the agent is working (uncertainty handled visually).

## Where the mandatory two live
- **Governor:** the pattern chip list includes `governor (cap: 1 change)` and the footer explains the safety cap.
- **Trust builder:** the confirm-card and result card name the exact change + keep the old slot until confirmed.

## Failure/uncertainty states (not just toasts)
The Assistant includes a full error card (badge style) with Retry **and** Dismiss, and the success path confirms before save — uncertainty is designed at each hand-off.

## Deliverable check
- 4+ named patterns implemented, including one governor and one trust builder → patterns 1 & 2 (plus 3–5).
- Failure and uncertainty states are designed, not just a toast → dedicated error card + streaming cursor + confirm-then-save.

## Repo links
- Assistant surface: `https://github.com/Eldasoky1/FlyRank-assignments/tree/master/assignments/UX-track-prototype`
- This file: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/UX-07-ai-surface/README.md`