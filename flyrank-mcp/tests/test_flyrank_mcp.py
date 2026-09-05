"""Tests for flyrank-mcp. A MockTransport stands in for the real portal."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

import flyrank_mcp.server as server
from flyrank_mcp.client import (
    DEFAULT_CAPSTONE_ROUTES,
    DEFAULT_ME_ROUTES,
    FlyRankClient,
    find_me,
    list_capstones,
    submit_capstone,
)
from flyrank_mcp.config import load_dotenv_file
from flyrank_mcp.registry import load_registry


def make_handler(routes: dict[str, object]):
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        query = request.url.query.decode() if request.url.query else ""
        key = f"{path}?{query}" if query else path
        value = routes.get(key)
        if value is None:
            return httpx.Response(404, json={"error": "not found"}, request=request)
        if isinstance(value, tuple):
            status, payload = value
        else:
            status, payload = 200, value
        return httpx.Response(status, json=payload, request=request)

    return handler


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("FLYRANK_BASE_URL", "https://portal.test")
    monkeypatch.setenv("FLYRANK_COOKIE", "session=testcookie123")
    monkeypatch.delenv("FLYRANK_API_TOKEN", raising=False)
    monkeypatch.setenv("FLYRANK_STATE_DIR", str(tmp_path))
    return tmp_path


def make_client(handler) -> FlyRankClient:
    return FlyRankClient(transport=httpx.MockTransport(handler))


# ---------------------------------------------------------------- config


def test_dotenv_file_loaded_when_var_unset(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "FLYRANK_BASE_URL=https://env.test\nFLYRANK_COOKIE=\"session=envval\"\n# comment\n\n"
    )
    monkeypatch.delenv("FLYRANK_BASE_URL", raising=False)
    monkeypatch.delenv("FLYRANK_COOKIE", raising=False)
    load_dotenv_file(env_file)
    assert __import__("os").environ["FLYRANK_BASE_URL"] == "https://env.test"
    assert __import__("os").environ["FLYRANK_COOKIE"] == "session=envval"


def test_process_env_wins_over_dotenv(env, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FLYRANK_COOKIE=session=fromfile")
    load_dotenv_file(env_file)
    assert __import__("os").environ["FLYRANK_COOKIE"] == "session=testcookie123"


# ---------------------------------------------------------------- client


def test_request_json_success_and_registry(env):
    routes = {"/api/capstones": {"items": [{"id": 1}]}}
    client = make_client(make_handler(routes))
    result = server_await(client.request("GET", "/api/capstones"))
    server_await(client.aclose())
    assert result["ok"] is True
    assert result["status"] == 200
    assert result["json"] == {"items": [{"id": 1}]}
    entries = load_registry(env)
    assert any(e["path"] == "/api/capstones" and e["method"] == "GET" for e in entries)


def test_request_non_json_text(env):
    def handler(request):
        return httpx.Response(200, text="<html>hello portal</html>", request=request)

    client = make_client(handler)
    result = server_await(client.request("GET", "/"))
    server_await(client.aclose())
    assert result["ok"] is True
    assert "content_type" in result
    assert "json" not in result
    assert "hello portal" in result["text"]


def test_request_500_is_not_ok(env):
    routes = {"/api/boom": (500, {"error": "internal"})}
    client = make_client(make_handler(routes))
    result = server_await(client.request("GET", "/api/boom"))
    server_await(client.aclose())
    assert result["ok"] is False
    assert result["status"] == 500


def test_request_network_error(env):
    def handler(request):
        raise httpx.ConnectError("connection refused")

    client = make_client(handler)
    result = server_await(client.request("GET", "/"))
    server_await(client.aclose())
    assert result["ok"] is False
    assert result["client_error"] is True
    assert "connection refused" in result["error"]


def test_auth_header_cookie_sent(env):
    captured = {}

    def handler(request):
        captured["cookie"] = request.headers.get("cookie")
        captured["authorization"] = request.headers.get("authorization")
        return httpx.Response(200, json={}, request=request)

    client = make_client(handler)
    server_await(client.request("GET", "/"))
    server_await(client.aclose())
    assert captured["cookie"] == "session=testcookie123"
    assert captured["authorization"] is None


def test_auth_header_bearer_used_when_cookie_absent(env, monkeypatch):
    monkeypatch.delenv("FLYRANK_COOKIE")
    monkeypatch.setenv("FLYRANK_API_TOKEN", "tok123")
    captured = {}

    def handler(request):
        captured["authorization"] = request.headers.get("authorization")
        return httpx.Response(200, json={}, request=request)

    client = make_client(handler)
    server_await(client.request("GET", "/"))
    server_await(client.aclose())
    assert captured["authorization"] == "Bearer tok123"


# ------------------------------------------------------- high-level ops


def test_find_me_falls_back_to_third_route(env):
    routes = {
        "/api/me": (404, {}),
        "/api/user/me": (404, {}),
        "/api/auth/me": (200, {"id": 7, "name": "Ahmed"}),
    }
    client = make_client(make_handler(routes))
    result = server_await(find_me(client))
    server_await(client.aclose())
    assert result["ok"] is True
    assert result["matched_route"] == "/api/auth/me"
    assert result["json"]["name"] == "Ahmed"


def test_list_capstones_failure_reports_tried_routes(env):
    client = make_client(make_handler({}))
    result = server_await(list_capstones(client))
    server_await(client.aclose())
    assert result["ok"] is False
    assert result["tried_routes"] == DEFAULT_CAPSTONE_ROUTES


def test_submit_capstone_success(env):
    routes = {"/api/capstones/submit": (201, {"status": "submitted"})}
    client = make_client(make_handler(routes))
    result = server_await(
        submit_capstone(
            client,
            name="Metering & Billing",
            repo_url="https://github.com/Eldasoky1/FlyRank-assignments",
            commit_sha="87f4655",
            notes="20 tests",
        )
    )
    server_await(client.aclose())
    assert result["ok"] is True
    assert result["status"] == 201
    assert result["sent_payload"]["commit_sha"] == "87f4655"


def test_submit_capstone_all_routes_fail_returns_best(env):
    client = make_client(make_handler({}))
    result = server_await(
        submit_capstone(
            client,
            name="X",
            repo_url="https://example.com/repo",
            commit_sha="abc",
        )
    )
    server_await(client.aclose())
    assert result["ok"] is False
    assert result["sent_payload"]["name"] == "X"
    assert "matched_route" in result


# ---------------------------------------------------------------- tools


def test_tool_flyrank_status_never_leaks_secret(env):
    body = json.loads(server_await(server.flyrank_status()))
    assert body["base_url"] == "https://portal.test"
    assert body["auth_mode"] == "cookie"
    assert "testcookie123" not in json.dumps(body)


def test_tool_flyrank_request_via_mock(env, monkeypatch):
    routes = {"/api/ping": {"pong": True}}

    async def fake_session(transport=None):
        return FlyRankClient(transport=httpx.MockTransport(make_handler(routes)))

    monkeypatch.setattr(server, "_session", fake_session)
    body = json.loads(
        server_await(
            server.flyrank_request(method="GET", path="/api/ping",
                                   json_body=None, params=None)
        )
    )
    assert body["ok"] is True
    assert body["json"] == {"pong": True}


def test_tool_flyrank_request_bad_json(env, monkeypatch):
    async def fake_session(transport=None):
        return FlyRankClient(transport=httpx.MockTransport(make_handler({})))

    monkeypatch.setattr(server, "_session", fake_session)
    with pytest.raises(ValueError):
        server_await(server.flyrank_request(json_body="not json"))


def test_tool_flyrank_health(env, monkeypatch):
    async def fake_session(transport=None):
        return FlyRankClient(
            transport=httpx.MockTransport(make_handler({"/": (200, {})}))
        )

    monkeypatch.setattr(server, "_session", fake_session)
    body = json.loads(server_await(server.flyrank_health()))
    assert body["reachable"] is True
    assert body["auth_configured"] is True


def test_tool_flyrank_fetch_page_html(env, monkeypatch):
    def handler(request):
        return httpx.Response(
            200,
            text="<html><head><title>Portal Dashboard</title></head><body>ready</body></html>",
            request=request,
        )

    async def fake_session(transport=None):
        return FlyRankClient(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(server, "_session", fake_session)
    body = json.loads(server_await(server.flyrank_fetch_page(path="/")))
    assert body["status"] == 200
    assert body["title"] == "Portal Dashboard"
    assert "ready" in body["text"]


# ---------------------------------------------------------------- helpers


def server_await(awaitable):
    import asyncio

    return asyncio.run(awaitable)