# AI Fluency — Week 7 · Hardening review (Submit)

**Deliverable:** the member genuinely tried to break their own site — real edge cases, not just the
happy path.

## Hardening pass — attempts + outcomes

Live site: `https://ahmed-eldasoky.pages.dev`. I tried to break it, in order:

| # | Attempt | Result |
| --- | --- | --- |
| 1 | Empty direct path: `/does-not-exist` | Serve 404 (Pages default) — site's own pages unaffected ✓ |
| 2 | `/cv` vs `/cv.html` (double slash, trailing variants) | 308 → `/cv` serves; no duplicate content ✓ |
| 3 | Malformed URLs with `?x=` and `#` junk | Pages route ignores query/hash; no state break ✓ |
| 4 | HTML/CSS injection via `?q=…` | No reflective rendering (static site, no params read) ✓ |
| 5 | Extreme widths (320px / 200% zoom / 4K) | Layout collapses to single column; no overflow ✓ |
| 6 | Keyboard-only (no mouse) | All links focusable; contrast maintained ✓ |
| 7 | Broken outbound links (mix of targets) | All three (GitHub/LinkedIn/mail) resolve ✓ |
| 8 | Asset abuse — deep `../` path | Pages serves 404; no traversal ✓ |

## Real edge cases found & fixed
- **Found:** foot-year script failed silently if JS disabled → **fixed:** the footer shows a static
  year with a `<noscript>` fallback (graceful either way).
- **Found:** two equal "CV" and "Contact" buttons competed (from design review) → **fixed:** one
  emphasized action; CV demoted to a neutral link.

## Deliverable check
- Genuinely tried to break their own site → 8-attempt table incl. traversal, injection, widths, keyboard.
- Real edge cases, not just happy path → the two found-and-fixed items.

## Repo link
`https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/AI-fluency-hardening/README.md`