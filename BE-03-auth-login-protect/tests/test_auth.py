"""End-to-end tests for the Auth API (BE-03).

These run against the in-memory MockAuthBackend so they work entirely
locally without a live Supabase project. The routes, validation and status
codes exercised here are identical to production.

Run (from this folder):
    python -m venv venv
    pip install -r requirements.txt
    pytest tests/ -q
"""

import os

# Force the mock backend: no real Supabase credentials => create_auth_backend()
# returns MockAuthBackend. Must happen before `import main`.
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""
os.environ["PORT"] = "8000"

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture(scope="module")
def client():
    return TestClient(main.app)


@pytest.fixture(scope="module")
def member(client):
    """Create one signed-up user and return its login response."""
    r = client.post("/auth/signup", json={"email": "a@b.com", "password": "secret123"})
    assert r.status_code == 201
    assert r.json()["user"]["email"] == "a@b.com"
    return client.post("/auth/login", json={"email": "a@b.com", "password": "secret123"}).json()


# ---- Stage 1: signup ----


def test_signup_returns_201(client):
    r = client.post("/auth/signup", json={"email": "new@b.com", "password": "secret123"})
    assert r.status_code == 201
    body = r.json()
    assert body["user"]["email"] == "new@b.com"
    assert "id" in body["user"]


def test_signup_missing_fields_400(client):
    assert client.post("/auth/signup", json={"email": "x@y.com"}).status_code == 422
    assert client.post("/auth/signup", json={"password": "secret123"}).status_code == 422


def test_signup_duplicate_email_400(client):
    r = client.post("/auth/signup", json={"email": "dup@b.com", "password": "secret123"})
    assert r.status_code == 201
    r2 = client.post("/auth/signup", json={"email": "dup@b.com", "password": "secret123"})
    assert r2.status_code == 400


# ---- Stage 1: login ----


def test_login_returns_tokens(client, member):
    assert member["access_token"]
    assert member["refresh_token"]
    assert member["user"]["email"] == "a@b.com"


def test_login_bad_credentials_401(client):
    r = client.post("/auth/login", json={"email": "a@b.com", "password": "wrongpass"})
    assert r.status_code == 401


def test_login_unknown_user_401(client):
    r = client.post("/auth/login", json={"email": "ghost@b.com", "password": "secret123"})
    assert r.status_code == 401


def test_login_missing_fields_422(client):
    assert client.post("/auth/login", json={"email": "a@b.com"}).status_code == 422
    assert client.post("/auth/login", json={"password": "x"}).status_code == 422


# ---- Stage 2: public route ----


def test_public_info_no_auth(client):
    r = client.get("/public/info")
    assert r.status_code == 200
    assert r.json() == {"message": "Welcome stranger! This info is public."}


# ---- Stage 3: token verification ----


def test_protected_profile_no_token_401(client):
    assert client.get("/protected/profile").status_code == 401


def test_protected_profile_bad_header_401(client):
    # "Basic" scheme instead of "Bearer" -> malformed
    r = client.get("/protected/profile", headers={"Authorization": "Basic abc"})
    assert r.status_code == 401


def test_protected_profile_invalid_token_401(client):
    r = client.get(
        "/protected/profile", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert r.status_code == 401


def test_protected_profile_valid_token_200(client, member):
    r = client.get(
        "/protected/profile",
        headers={"Authorization": f"Bearer {member['access_token']}"},
    )
    assert r.status_code == 200
    assert r.json()["user"]["email"] == "a@b.com"


# ---- Stage 4: middleware + dashboard + logout ----


def test_dashboard_protected_with_valid_token(client, member):
    r = client.get(
        "/protected/dashboard",
        headers={"Authorization": f"Bearer {member['access_token']}"},
    )
    assert r.status_code == 200
    assert r.json()["user"]["email"] == "a@b.com"
    assert "widgets" in r.json()["dashboard"]


def test_dashboard_protected_no_token_401(client):
    assert client.get("/protected/dashboard").status_code == 401


def test_logout_returns_204(client):
    login = client.post(
        "/auth/login", json={"email": "a@b.com", "password": "secret123"}
    ).json()
    r = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )
    assert r.status_code == 204


def test_logout_no_token_401(client):
    assert client.post("/auth/logout").status_code == 401


def test_logout_revokes_token(client):
    login = client.post(
        "/auth/login", json={"email": "a@b.com", "password": "secret123"}
    ).json()
    token = login["access_token"]
    assert (
        client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"}).status_code
        == 204
    )
    r = client.get("/protected/profile", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


# ---- Stage 5: Swagger / security scheme ----


def test_docs_served(client):
    r = client.get("/docs")
    assert r.status_code == 200


def test_openapi_has_bearer_security(client):
    spec = client.get("/openapi.json").json()
    schemes = spec.get("components", {}).get("securitySchemes", {})
    assert any("bearer" in k.lower() or "http" in k.lower() for k in schemes)
    # Protected routes must require the bearer security
    profile = spec["paths"]["/protected/profile"]
    assert profile["get"].get("security")
