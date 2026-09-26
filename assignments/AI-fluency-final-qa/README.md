# AI Fluency — Week 6 · Build+ Final QA

**Deliverable (Build+):** all links work (including demo/repo); no oversized images; nothing
obviously broken on any width.

## QA done on the live site
Site: `https://ahmed-eldasoky.pages.dev` (source: `assignments/PF-04-personal-website/site/`).

### Links — all working
| Link | Target | Result |
| --- | --- | --- |
| GitHub | `github.com/Eldasoky1/…` | ✓ opens |
| LinkedIn | real public profile | ✓ opens |
| Email | `mailto:` | ✓ opens mail client |
| CV | `/cv.html` → `/cv` (Pages 308) | ✓ serves |
| Footer echo | inline only | ✓ |

### Images / weight
- **No external images** — the site ships **zero `<img>` tags** except none; the hero is text, so
  there is no oversized-image risk by construction. CSS is inline (single file, ~5 KB).

### Responsive (any width)
- Single column layout uses `clamp()`-based type; cards stack; no horizontal scroll observed at
  360, 768, or 1440 px. Touch targets ≥ 44 px.

## Deliverable check
- All links work incl. demo/repo → tested ✓
- No oversized images → none present (text hero) ✓
- Nothing broken on any width → checked 360/768/1440 ✓

## Repo links
- Site: `https://github.com/Eldasoky1/FlyRank-assignments/tree/master/assignments/PF-04-personal-website/site`
- This file: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/AI-fluency-final-qa/README.md`