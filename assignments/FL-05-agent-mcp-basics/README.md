# FL-05 — Agent Concepts and MCP Basics

Vector of the FL-05 assignment: workflow-vs-agent distinction applied to my own FL-04 build,
the MCP three primitives, and evidence of one working MCP server doing real tool calls.

- `explainer.md` — 677-word explainer (own words): workflow vs agent, MCP tools/resources/
  prompts, the concrete changes FL-04 needs to become an agent (one named first upgrade:
  model-driven topic selection).
- `mcp-evidence.md` — one live JSON-RPC MCP session against the `flyrank` MCP server (see
  `../../flyrank-mcp`): `tools/list` + three tool calls with server-side results that a chat
  client alone cannot perform (authenticated live query, local registry read, live page
  fetch), plus reproduction steps.

Evidence style note: transcripts capture `name → arguments → content` exactly; Claude
Desktop screenshots of the same three calls can be added by pasting the stdio command from
`mcp-evidence.md` §5.