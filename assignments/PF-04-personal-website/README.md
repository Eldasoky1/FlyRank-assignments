# PF-04 — Personal Website live on Cloudflare Pages

**Deliverable:** `https://ahmed-eldasoky.pages.dev` — live over HTTPS on a free, CV-worthy `pages.dev` URL.

This assignment is "Personal Website Live on the FlyRank Domain" (Week 5). The site is hosted on **Cloudflare Pages** (free tier, accepted host), written by hand as plain HTML/CSS so that every deployed file is fully understood.

## Files in this folder — what each one is

```
PF-04-personal-website/
├── site/                      #  the exact files deployed to Cloudflare Pages
│   ├── index.html             #  home page: hero, about, "what I build", links
│   └── cv.html                #  curriculum vitae page (linked as "CV" from index)
├── dns-walkthrough.md         #  ~1 page, non-technical: what DNS does, what a CNAME is,
│                              #  and the resolver → nameserver → record → response journey
└── README.md                  #  this file
```

### `site/index.html`
The entire site on one page to keep it easy to audit and explain. Everything is inline:

- **No frameworks, no build step** — what you see is what is served.
- Inline CSS defines a small design-token set (background, panel, accent `#07f49e`, text/muted) instead of a dependency.
- Sections: eyebrow + name + tagline → links row → "What I build" (three cards: MCP, backend architecture, automation) → "Now" (FlyRank, E-JUST, open source) → footer.
- Links: GitHub, LinkedIn, Email, CV (→ `/cv.html`), and a booking link.
- A tiny inline script renders the current year in the footer; one file, fully readable.

### `site/cv.html`
A self-contained CV page (professional print-friendly styling, no dependencies): profile, FlyRank internship, E-JUST education, projects, skills. Real facts taken from the intern profile and GitHub; kept deliberately simple so the author can replace it with an official CV later.

### `dns-walkthrough.md`
The mandatory DNS write-up — see that file. Summary: DNS is the internet's phonebook; a **CNAME** aliases one name to another (so a registrar's `CNAME → ahmed-eldasoky.pages.dev` needs no IP knowledge); the journey is *local cache → recursive resolver → hierarchy of nameservers → authoritative record → IP → HTTPS connection*.

## Honest notes (what the human must still do)

- **Book a call** link currently points to `mailto:` with a booking subject. Swap it for a real scheduler (e.g. Calendly) URL when one exists.
- **CV** is this repo's `cv.html`; replace with the official CV (e.g. the one in the portal's profile) when ready.
- **LinkedIn + the site link**: the assignment also requires the site to be linked *from* LinkedIn and the CV. The LinkedIn URL used here is the real public profile; adding the site URL to that profile is a manual, account-owner action — flagged here rather than faked.

## How it was deployed (reproducible)

Two credentials, two jobs:

**1. Assets** (scoped upload JWT, only valid ~30 min):
- `GET /accounts/{account}/pages/projects/ahmed-eldasoky/upload-token` → short-lived JWT.
- Per file, key = `blake3( base64(file_content) + file_ext )` truncated to 32 hex chars (the convention the build service expects).
- `POST /accounts/{account}/pages/projects/ahmed-eldasoky/pages/assets/upload` (JWT auth) with a JSON array `[{ "key": <32-hex>, "value": "<base64>", "metadata": { "contentType": "text/html" }, "base64": true }]`, then `POST …/pages/assets/upsert-hashes` with `{ "hashes": [ … ] }`.

**2. Deployment** (account credential, NOT the upload JWT — it is rejected with `9106 Authentication failed`):
- `POST /accounts/{account}/pages/projects/ahmed-eldasoky/deployments` (account token) with a `multipart/form-data` body:
  - part `branch` = `main`,
  - part `manifest` = `{ "/index.html": <32-hex>, "/cv.html": <32-hex> }` — **leading-slash keys**, values = the asset keys from step 1.

**Result:** `https://ahmed-eldasoky.pages.dev` serves with an auto-issued HTTPS certificate (no CNAME needed here — the `pages.dev` domain is already Cloudflare's own; see `dns-walkthrough.md` for what a CNAME adds on a custom domain).

Notes:
- The upload JWT **can't** create deployments; the account key **can**, but it does not put file *content* into the deployment — content comes from the asset store via the manifest, so assets must exist first.
- Pages clean-URLs by default: `/cv.html` 308-redirects to `/cv`, which serves the CV. The site's `index.html` links to `/cv.html` and works through that redirect.

A fresh deployment: write the files → recompute the 32-hex blake3 keys → re-upload assets → upsert → POST a new deployment.