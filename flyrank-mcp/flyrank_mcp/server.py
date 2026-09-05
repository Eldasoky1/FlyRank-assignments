"""MCP server exposing the FlyRank portal to the agent.

Tools
-----
flyrank_health             reachability + credential status
flyrank_status             config overview (never prints secrets)
flyrank_request            generic request / endpoint discovery engine
flyrank_endpoints          discovered + candidate routes
flyrank_me                 best-effort current-profile fetch
flyrank_list_capstones     best-effort capstone list fetch
flyrank_submit_capstone    best-effort capstone submission
flyrank_fetch_page         HTML fallback when no JSON API exists

Spawn with `flyrank-mcp` (installed console script) over stdio.
"""

from __future__ import annotations

import json
import re

import httpx
from mcp.server.fastmcp import FastMCP

from .client import (
    DEFAULT_CAPSTONE_ROUTES,
    DEFAULT_ME_ROUTES,
    DEFAULT_SUBMIT_ROUTES,
    FlyRankClient,
    find_me,
    list_capstones,
    submit_capstone,
)
from .config import get_config
from .registry import load_registry

mcp = FastMCP("flyrank")


def _box(data) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)


def _parse_json_arg(raw: str | None, what: str) -> dict | None:
    if raw is None or raw.strip() == "":
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{what} is not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{what} must be a JSON object")
    return parsed


async def _session(transport: httpx.AsyncBaseTransport | None = None) -> FlyRankClient:
    return FlyRankClient(transport=transport)


@mcp.tool()
async def flyrank_health() -> str:
    """Check that the FlyRank portal is reachable and whether credentials are configured."""
    client = await _session()
    try:
        result = await client.request("GET", "/")
        return _box(
            {
                "reachable": result.get("client_error") is not True,
                "base_url": client.config.base_url,
                "portal_status": result.get("status"),
                "auth_mode": client.config.auth_mode,
                "auth_configured": client.config.auth_configured,
                "note": "auth_mode 'none' means only public endpoints will work.",
            }
        )
    finally:
        await client.aclose()


@mcp.tool()
async def flyrank_status() -> str:
    """Show MCP config: base URL, auth mode, state dir, and discovered endpoints. Never prints secrets."""
    cfg = get_config()
    return _box(
        {
            "base_url": cfg.base_url,
            "auth_mode": cfg.auth_mode,
            "auth_configured": cfg.auth_configured,
            "state_dir": str(cfg.state_dir),
            "registered_endpoints": load_registry(cfg.state_dir),
        }
    )


@mcp.tool()
async def flyrank_request(
    method: str = "GET",
    path: str = "/",
    json_body: str | None = None,
    params: str | None = None,
) -> str:
    """Send an arbitrary request to the FlyRank portal (the discovery engine).

    method: GET, POST, PUT, PATCH, DELETE or HEAD.
    path: absolute path, e.g. "/api/capstones" (must start with "/").
    json_body: optional JSON object string, used for POST/PUT/PATCH.
    params: optional JSON object string of query parameters.

    Successful (2xx) responses are recorded in the endpoint registry, so
    discovered routes are visible via flyrank_endpoints later.
    """
    body = _parse_json_arg(json_body, "json_body")
    query = _parse_json_arg(params, "params")
    client = await _session()
    try:
        return _box(await client.request(method.upper(), path, json_body=body, params=query))
    finally:
        await client.aclose()


@mcp.tool()
async def flyrank_endpoints() -> str:
    """List endpoints discovered so far, plus the candidate routes high-level tools try."""
    cfg = get_config()
    return _box(
        {
            "discovered": load_registry(cfg.state_dir),
            "candidate_routes": {
                "me": DEFAULT_ME_ROUTES,
                "capstones": DEFAULT_CAPSTONE_ROUTES,
                "submit": DEFAULT_SUBMIT_ROUTES,
            },
        }
    )


@mcp.tool()
async def flyrank_me() -> str:
    """Fetch the logged-in user's profile. Tries conventional endpoints; use flyrank_request if it misses."""
    client = await _session()
    try:
        return _box(await find_me(client))
    finally:
        await client.aclose()


@mcp.tool()
async def flyrank_list_capstones() -> str:
    """List capstones / track assignments for the logged-in user. Best-effort route discovery."""
    client = await _session()
    try:
        return _box(await list_capstones(client))
    finally:
        await client.aclose()


@mcp.tool()
async def flyrank_submit_capstone(
    name: str,
    repo_url: str,
    commit_sha: str = "",
    notes: str = "",
    track: str = "backend-ai",
    endpoint: str = "",
) -> str:
    """Submit a capstone (repo link + commit) to the FlyRank portal.

    Tries conventional submit routes first; pass `endpoint` once
    flyrank_request/flyrank_endpoints have revealed the real route.
    """
    client = await _session()
    try:
        return _box(
            await submit_capstone(
                client,
                name=name,
                repo_url=repo_url,
                commit_sha=commit_sha,
                notes=notes,
                track=track,
                endpoint=endpoint,
            )
        )
    finally:
        await client.aclose()


@mcp.tool()
async def flyrank_fetch_page(path: str = "/") -> str:
    """Fetch an HTML page from the portal (fallback when no JSON API exists). Returns title + trimmed text."""
    client = await _session()
    try:
        response = await client.client.get(path)
        ok = 200 <= response.status_code < 300
        title = ""
        match = re.search(
            r"<title[^>]*>(.*?)</title>", response.text, re.IGNORECASE | re.DOTALL
        )
        if match:
            title = match.group(1).strip()
        plain = re.sub(r"<[^>]+>", " ", response.text)
        plain = re.sub(r"\s+", " ", plain).strip()
        return _box(
            {
                "ok": ok,
                "status": response.status_code,
                "final_url": str(response.url),
                "title": title,
                "text": (plain[:6000] + "...") if len(plain) > 6000 else plain,
            }
        )
    except httpx.HTTPError as exc:
        return _box({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
    finally:
        await client.aclose()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()