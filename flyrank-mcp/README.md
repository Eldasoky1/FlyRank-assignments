# flyrank-mcp

An [MCP](https://modelcontextprotocol.io) server that gives AI agents
programmatic access to the **FlyRank AI Internship portal**
(`internship.flyrank.ai`) — including endpoint discovery and best-effort
capstone submission.

## Why this exists

The FlyRank portal's real API is not publicly documented and sits behind
login. Instead of hard-coding one guessed route shape, this server is
**configuration-driven**:

- credentials are loaded from your environment or a local `.env`;
- a generic `flyrank_request` tool lets the agent probe the portal and
  discover the real endpoints at runtime;
- successful discoveries are recorded to a persistent registry
  (`~/.flyrank-mcp/endpoints.json`), so findings survive restarts;
- high-level tools (`flyrank_me`, `flyrank_list_capstones`,
  `flyrank_submit_capstone`) try conventional routes and degrade to clear
  guidance when they miss.

## Tools

| Tool | Purpose |
| --- | --- |
| `flyrank_health` | Portal reachability + credential status |
| `flyrank_status` | Config overview (never prints secrets) |
| `flyrank_request` | Generic request / endpoint discovery engine |
| `flyrank_endpoints` | Discovered + candidate routes |
| `flyrank_me` | Fetch current profile (best-effort) |
| `flyrank_list_capstones` | List capstones / assignments (best-effort) |
| `flyrank_submit_capstone` | Submit a capstone with repo URL + commit SHA |
| `flyrank_fetch_page` | HTML fallback when no JSON API exists |

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m pytest -q
```

## Credentials (do this yourself — never paste secrets into a chat)

Copy `.env.example` to `.env` in this directory (it is gitignored) and fill
in **your** values, then restart opencode:

```
FLYRANK_BASE_URL=https://internship.flyrank.ai
FLYRANK_COOKIE=session=....      # login in a browser, copy the Cookie value
# or, if the portal issues tokens:
# FLYRANK_API_TOKEN=....
```

Priority: `FLYRANK_COOKIE` > `FLYRANK_API_TOKEN`. With neither set, the
server still starts and works against public endpoints.

## Register in opencode

Add to your opencode config (`~/.config/opencode/opencode.json`):

```json
"flyrank": {
  "type": "local",
  "command": ["C:\\Users\\engAh\\AppData\\Local\\Temp\\opencode\\FlyRank-assignments\\flyrank-mcp\\.venv\\Scripts\\flyrank-mcp.exe"],
  "enabled": true
}
```

Then **quit and restart opencode** (config is loaded at startup, not
hot-reloaded).

## Workflow

1. `flyrank_health` — confirm reachability + `auth_configured: true`.
2. `flyrank_status` / `flyrank_endpoints` — inspect known routes.
3. `flyrank_request` — discover the real API (e.g. probe `/api/capstones`,
   `/api/assignments`, the submit route).
4. `flyrank_submit_capstone` — submit once the real route is known
   (pass `endpoint`).

## Security notes

- The repo never contains secrets: `.env` is gitignored, and no tool
  returns the cookie/token value.
- The registry stores only paths, methods, status codes and timestamps.
- Credentials live only in your local `.env` / environment.