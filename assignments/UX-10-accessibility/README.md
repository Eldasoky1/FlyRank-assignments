# UX-10 — Accessibility and polish pass

## What was checked and fixed
- **Colour contrast (WCAG AA):** text (#0f172a) on bg/surface passes 4.5:1+; primary (#2563eb) on white 4.6:1; mute text bumped to #64748b (4.75:1 on #ffffff). Status is never color-only — every state also has a text label (chip “ok / danger / warn” with labels, not just colour).
- **Keyboard:** all tabs, buttons and form fields reachable by Tab; focus-visible outline on every control; Escape closes nothing trapped.
- **Screen reader:** inputs carry real `<label>`s (or `aria-label`), interactive textareas labelled; `aria-live="polite"` on the chat; `aria-selected` on tabs; `role="tablist"/"tab"`; hidden empty skeleton is `aria-hidden`.
- **Touch targets:** buttons ≥ 44px (padding, 40px+), adequate spacing.
- **Reduced motion:** the only motion is the streaming cursor; skeletons are layout-stable (no CLS) so they don’t trigger motion issues.

## Polish pass checklist
- Semantic HTML (main/header/nav/section) + landmarks ✓
- Consistent radius/padding from tokens (UX-05) ✓
- Every interactive element labelled ✓

## Deliverable check
- Accessibility + polish pass documented with real fixes → bullets above; all applied in the prototype.

## Repo links
- Prototype: `https://github.com/Eldasoky1/FlyRank-assignments/tree/master/assignments/UX-track-prototype`
- This file: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/UX-10-accessibility/README.md`