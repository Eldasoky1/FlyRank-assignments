# FL-05 — MCP evidence: three tool-calling tasks chat alone could not do

**Server used:** `flyrank` — the MCP server I built for this repository
(`../..` flyrank-mcp, Python/FastMCP). Any MCP client can connect to it via stdio; this
evidence is a real JSON-RPC 2.0 session I drove over standard I/O on 2026-09-06:

```
C:\...\FlyRank-assignments\flyrank-mcp\.venv\Scripts\python.exe -m flyrank_mcp.server
```

The session first negotiated `initialize` (protocol version 2024-11-05), then listed the
server's tools, then invoked three tools. Full transcript below. Each result is a server-side
tool execution — not a chat answer. This is what FL-05 asks to demonstrate: output that shows
**tool use**, with real side effects only a connector can reach.

## 1. `tools/list` — the server's surface

```
-> tools/list
<- [
     flyrank_health, flyrank_status, flyrank_request, flyrank_endpoints,
     flyrank_me, flyrank_list_capstones, flyrank_submit_capstone, flyrank_fetch_page
   ]
```

## 2. Task 1 — query a live, authenticated service

```
-> tools/call  flyrank_health  {}
<- isError: false
{
  "reachable": true,
  "base_url": "https://internship.flyrank.ai",
  "portal_status": 200,
  "auth_mode": "cookie",
  "auth_configured": true,
  "note": "auth_mode 'none' means only public endpoints will work."
}
```

**Why chat alone couldn't do this:** the portal requires a session cookie the server holds;
a plain chat client has no cookie jar and no network path to that origin. The tool performed
a real HTTPS round-trip and returned live reachability + credential state.

## 3. Task 2 — read local config state from disk

```
-> tools/call  flyrank_status  {}
<- isError: false
{
  "base_url": "https://internship.flyrank.ai",
  "auth_mode": "cookie",
  "auth_configured": true,
  "state_dir": "C:\\Users\\engAh\\.flyrank-mcp",
  "registered_endpoints": [
    { "method": "GET", "path": "/",                        "status": 200, "hits": 2, ... },
    { "method": "GET", "path": "/api/auth/session",        "status": 200, "hits": 3, ... },
    { "method": "GET", "path": "/api/auth/providers",      "status": 200, "hits": 3, ... },
    { "method": "GET", "path": "/api/auth/csrf",           "status": 200, "hits": 1, ... },
    { "method": "GET", "path": "/intern",                  "status": 200, "hits": 3, ... },
    { "method": "GET", "path": "/apply",                   "status": 200, "hits": 1, ... },
    { "method": "GET", "path": "/intern/submissions",      "status": 200, "hits": 2, ... }
    ... (endpoint registry: base/port/routes accumulated from real requests)
  ]
}
```

**Why chat alone couldn't do this:** this reads files under `.flyrank-mcp` on my machine —
the endpoint registry persisted by the MCP server. A chat client has no filesystem access.
The registry contents are data only real requests produced.

## 4. Task 3 — fetch and parse a live page (HTML → structured result)

```
-> tools/call  flyrank_fetch_page  { "path": "/intern/assignments?week=all&lane=foundation" }
<- isError: false
{
  "ok": true,
  "status": 200,
  "final_url": "https://internship.flyrank.ai/intern/assignments?week=all&lane=foundation",
  "title": "FlyRank AI Internship",
  "text": "Intern Start Dashboard Profile Onboarding Anthropic Certs Program Tracks
           Assignments Schedule Events ... AE Ahmed Eldasoky Intern
           ahmed.320240024@ejust.edu.eg ... FL-01 FL-02 FL-04 FL-05 FL-06 FL-07 FL-09 PF-04
           ... requ[...abridged...]"
}
```

**Why chat alone couldn't do this:** the page (450 KB of RSC payload) exists behind the same
authenticated origin; the tool fetched it live, validated the HTTP 200, extracted the
document title and stripped the markup to text — including the eight assignment codes on my
assignments page. No chat session can reach "my logged-in assignments page" without a
connector carrying the session.

## 5. How to reproduce

1. `cd flyrank-mcp`
2. `pip install -e .` (installs `flyrank-mcp` console script; or run directly)
3. Start the client of your choice — Claude Desktop, an IDE with MCP enabled, or the stdio
   session script `fr_mcp_proof3.py` used here — pointed at `python -m flyrank_mcp.server`.
4. Call `flyrank_health`, `flyrank_status`, and `flyrank_fetch_page` as above.

Optional screenshots: if you want UI screenshots of these three tool calls as FL-05's
screenshot evidence, connect Claude Desktop to the same stdio command and capture the tool
call cards; the transcripts above are the machine-readable equivalent and show the same
tool use (`name`, `arguments`, `content`).