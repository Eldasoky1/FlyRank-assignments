# CLAUDE.md — StreamChat (Frontend AI Engineering capstone)

## Project
- Small AI chat with a single `check_dates` tool; streaming reply; tool confirmation.
- Stack: Vite 5 + React 18 + Tailwind 3 (semantic tokens) + Vitest/Testing Library + Playwright.

## Commands
- `npm run dev` — Vite on :5198 (mock API must run on :5199 separately).
- `node api/mock.js` — SSE mock backend (:5199).
- `npm run test` — component tests (15).
- `npm run e2e` — Playwright (starts mock + preview).
- `npm run build` / `npm run preview` — production build.

## Conventions
- Components in `src/components/`, hooks in `src/hooks/`, tests colocated `*.test.jsx`.
- Test setup resets `window.__SABOTAGE` after each test.
- Query by role/label/testid, never by CSS class (see FE-09 rubric).
- Tool UI is a 4-state machine; never render a crashing state for `/error`.
- Streaming text is buffered; never render half-finished markdown.

## Env
- `VITE_CHAT_ENDPOINT`, `VITE_HEALTH_ENDPOINT` (optional; default `/api/chat`, `/api/health`).
- Do not commit `node_modules/`, `dist/`, `.env`, test artifacts.