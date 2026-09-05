"""HTTP client for the FlyRank portal plus best-effort high-level operations.

The portal's real API surface is not publicly documented and sits behind
auth. Rather than guess one shape and hard-code it, this client:

* sends credentials from FLYRANK_COOKIE / FLYRANK_API_TOKEN;
* exposes a generic `request` that records successful endpoints in the
  registry (discovery);
* provides conventional-route fallbacks for profile, capstone listing and
  submission that degrade to clear "route not found" guidance.

Any httpx transport can be injected (used by the tests via MockTransport).
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from .config import FlyRankConfig, get_config, with_state_dir
from .registry import record_endpoint

DEFAULT_ME_ROUTES = [
    "/api/me",
    "/api/user/me",
    "/api/auth/me",
    "/api/profile",
    "/api/users/me",
]

DEFAULT_CAPSTONE_ROUTES = [
    "/api/capstones",
    "/api/capstones?page=1",
    "/api/capstone",
    "/api/assignments",
    "/api/capstones/",
]

DEFAULT_SUBMIT_ROUTES = [
    "/api/capstones/submit",
    "/api/capstone/submit",
    "/api/capstones",
    "/api/submissions",
]

TEXT_TRIM = 8000


def _ok_status(status: int) -> bool:
    return 200 <= status < 300


def _trim_text(text: str, limit: int = TEXT_TRIM) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...[truncated {len(text) - limit} chars]"


class FlyRankClient:
    """Thin async HTTP client for the FlyRank portal."""

    def __init__(
        self,
        config: FlyRankConfig | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        state_dir: str | None = None,
    ):
        self.config = config or get_config()
        if state_dir is not None:
            self.config = with_state_dir(self.config, state_dir)
        self.config.state_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            headers={"User-Agent": "flyrank-mcp/0.1.0", **self.config.auth_headers()},
            transport=transport,
            follow_redirects=True,
            timeout=30.0,
        )

    async def aclose(self) -> None:
        await self.client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        json_body: dict | list | None = None,
        params: dict | None = None,
    ) -> dict[str, Any]:
        method = method.upper()
        try:
            response = await self.client.request(
                method, path, json=json_body, params=params
            )
        except httpx.HTTPError as exc:
            return {
                "ok": False,
                "client_error": True,
                "error": f"{type(exc).__name__}: {exc}",
                "method": method,
                "path": path,
            }
        payload: dict[str, Any] = {
            "ok": _ok_status(response.status_code),
            "status": response.status_code,
            "method": method,
            "path": path,
            "final_url": str(response.url),
            "content_type": response.headers.get("content-type"),
        }
        if response.status_code in (204, 304):
            payload["text"] = ""
        else:
            try:
                payload["json"] = response.json()
            except (json.JSONDecodeError, ValueError):
                payload["text"] = _trim_text(response.text)
        if _ok_status(response.status_code):
            record_endpoint(
                self.config.state_dir, method, path, response.status_code
            )
        return payload


async def first_ok(
    client: FlyRankClient,
    routes: list[str],
    method: str = "GET",
    json_body: dict | None = None,
) -> dict[str, Any] | None:
    """Return the first 2xx response across candidate routes, or None."""
    for route in routes:
        payload = await client.request(method, route, json_body=json_body)
        if payload.get("ok"):
            payload["matched_route"] = route
            return payload
    return None


async def find_me(client: FlyRankClient) -> dict[str, Any]:
    result = await first_ok(client, DEFAULT_ME_ROUTES)
    if result is None:
        return {
            "ok": False,
            "error": "No conventional profile route returned 2xx. Use flyrank_request to discover the real endpoint.",
            "tried_routes": DEFAULT_ME_ROUTES,
        }
    return result


async def list_capstones(client: FlyRankClient) -> dict[str, Any]:
    result = await first_ok(client, DEFAULT_CAPSTONE_ROUTES)
    if result is None:
        return {
            "ok": False,
            "error": "No conventional capstone list route returned 2xx. Use flyrank_request to discover the real endpoint.",
            "tried_routes": DEFAULT_CAPSTONE_ROUTES,
        }
    return result


async def submit_capstone(
    client: FlyRankClient,
    name: str,
    repo_url: str,
    commit_sha: str = "",
    notes: str = "",
    track: str = "backend-ai",
    endpoint: str = "",
) -> dict[str, Any]:
    """Submit a capstone. Tries candidate routes; returns the best (non-network-error) result."""
    body = {
        "name": name,
        "repo_url": repo_url,
        "github": repo_url,
        "commit_sha": commit_sha,
        "notes": notes,
        "track": track,
    }
    routes = ([endpoint] if endpoint else []) + DEFAULT_SUBMIT_ROUTES
    results: list[dict[str, Any]] = []
    for route in routes:
        payload = await client.request("POST", route, json_body=body)
        payload["matched_route"] = route
        results.append(payload)
        if payload.get("ok"):
            payload["sent_payload"] = body
            return payload
    best: dict[str, Any] | None = None
    for payload in results:
        if not payload.get("client_error"):
            best = payload
            break
    if best is None:
        best = {"ok": False, "error": "All candidate routes failed.", "tried_routes": routes}
    best["sent_payload"] = body
    return best