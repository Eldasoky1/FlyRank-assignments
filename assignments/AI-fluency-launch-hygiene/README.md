# AI Fluency — Week 7 · Launch hygiene (Build+)

**Deliverable:** launch hygiene — social-share preview, favicon, and page titles; open the final
address on a phone once more.

## Hygiene checks

### 1. Social-share preview
- **Repo/folder:** the deployed `pages.dev` site is served by Cloudflare Pages; Pages auto-supplies
  meta used by social scrapers. My `index.html` includes a real `<title>`, meta `description`, and
  `og:`/`twitter:` tags (title, description, image) so a shared link renders a card, not a bare URL.
- **Note (honest):** `og:image` points to a public PNG hosted beside the pages (added in the
  deploy); the share card text is verified via the standard `og:` fields.

### 2. Favicon
- Added a real `favicon.svg` (accent mark on the kit's background) linked in `<head>`; verified it
  loads in the browser tab (no 404).

### 3. Page titles
- `index.html` → `Ahmed El-Dasoky — Backend & AI Integrations`
- `cv.html` → `Ahmed El-Dasoky — CV`
- Unique, short, and keyword-correct on both pages.

### 4. On-phone pass
- Opened `https://ahmed-eldasoky.pages.dev` on a phone (mobile viewport): hero, case cards, CV link,
  and CTA all render; accent contrast holds; single-column layout has no horizontal scroll.

## Deliverable check
- Share preview, favicon, and titles are correct on the real address → sections 1–3 above, applied live.
- Phone re-check of the final address → section 4.

## Repo links
- Site source: `https://github.com/Eldasoky1/FlyRank-assignments/tree/master/assignments/PF-04-personal-website/site`
- This file: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/AI-fluency-launch-hygiene/README.md`