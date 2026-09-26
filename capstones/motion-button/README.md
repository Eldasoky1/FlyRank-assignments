# Motion Button — full-lifecycle button with intentional motion

Capstone (CUSTOM-MRIGS9RF). See `index.html`.

- Openable standalone: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/capstones/motion-button/index.html`
- Live demo mirrors this single-file page (host the folder statically).
- Deliberate states: **idle → busy → success | error**, each with distinct label, motion, and ARIA
  `role="status"` live region. The demo includes **triggers that force Success, Error, Busy, and
  Reset on demand** so reviewers can see both outcomes without relying on randomness.

## Deliverables check
- Live URL / sandbox demo page with success & failure triggers → `index.html` buttons
  "Force success", "Force error", "Force busy", "Reset".

## Perf note
- Single HTML file, no build step, no libraries → starts instantly; motion is CSS-only transform/
  opacity on a composited layer (no layout thrash), within budget.