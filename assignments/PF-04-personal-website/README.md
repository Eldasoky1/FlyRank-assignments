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

1. API on the account: create Pages project `ahmed-eldasoky` (production branch `main`).
2. `GET /accounts/{account}/pages/projects/ahmed-eldasoky/upload-token` → short-lived JWT.
3. `POST /accounts/{account}/pages/projects/ahmed-eldasoky/deployments` with a `multipart/form-data` body:
   - part `manifest` = `{ "index.html": <sha256>, "cv.html": <sha256> }`,
   - one part per file, named by its content hash, file content as the value.
4. Cloudflare serves the deployment at `https://ahmed-eldasoky.pages.dev` with an auto-issued HTTPS certificate (no custom domain needed — and no CNAME involved in this case; see `dns-walkthrough.md` for what a CNAME would add).

A fresh deployment would be: write the files → recompute the sha256 hashes → repeat step 2 and 3.