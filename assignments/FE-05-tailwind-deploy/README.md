# FE-05 — Tailwind, design tokens, deploy pipeline, health check

Implemented in the capstone app.

## What was done
- **Tailwind installed + base**: `frontend-capstone/tailwind.config.js` (semantic tokens) and
  `src/index.css` (@tailwind directives + font/color base).
- **Design tokens**: semantic palette (`ink`, `paper`, `accent`, `danger`, `ok` with `*-soft`
  variants), `font-family`, `border-radius.control/chip`, `box-shadow.card` — used consistently
  across the app so future components opt into the system instead of ad-hoc colors.
- **Deploy pipeline**: Vite build produces static `dist/` (works on Vercel/Netlify/CF Pages);
  `vite.config.js` proxied environment with `VITE_*` env vars documented in the README.
- **Health-check page**: `src/components/HealthCheck.jsx` fetches `/api/health`
  (`api/mock.js`) and renders ok/error states; accessible `role="alert"` for failure.

## Deliverable check
| Criterion | Where |
| --- | --- |
| Preview URL loads, no build errors | `npm run build` passes; `npm run preview` |
| Tailwind + tokens | `frontend-capstone/tailwind.config.js`, `src/index.css` |
| Health-check page rendering fetched data | `frontend-capstone/src/components/HealthCheck.jsx` |

## Repo links
- App root: `https://github.com/Eldasoky1/FlyRank-assignments/tree/master/frontend-capstone`
- Health check: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/frontend-capstone/src/components/HealthCheck.jsx`