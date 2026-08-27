"""Supabase Auth client wrapper.

Encapsulates every Supabase call the API makes behind a small `AuthBackend`
interface. The FastAPI routes depend on this interface, never on the Supabase
SDK directly. There are two implementations:

- `SupabaseAuthBackend`  -> the real Supabase client (production)
- `MockAuthBackend`      -> an in-memory fake used by the test-suite so the
                            API is verifiable locally without a live Supabase.

Swapping backend is a single line in `create_auth_backend()`.
"""

from __future__ import annotations

from typing import Optional

from supabase import create_client

from config import Settings


class User:
    """Minimal user value object returned by the auth backend."""

    def __init__(self, id: str, email: str, metadata: dict):
        self.id = id
        self.email = email
        self.metadata = metadata

    def to_dict(self) -> dict:
        return {"id": self.id, "email": self.email, **self.metadata}


class AuthResult:
    """Result of a successful sign up / login."""

    def __init__(self, user: User, access_token: str, refresh_token: str):
        self.user = user
        self.access_token = access_token
        self.refresh_token = refresh_token


class SupabaseError(Exception):
    """Raised when the auth backend rejects an operation."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


class AuthBackend:
    """Interface the routes depend on."""

    def sign_up(self, email: str, password: str) -> AuthResult:
        raise NotImplementedError

    def login(self, email: str, password: str) -> AuthResult:
        raise NotImplementedError

    def logout(self, access_token: str) -> None:
        raise NotImplementedError

    def get_user(self, access_token: str) -> Optional[User]:
        raise NotImplementedError


class SupabaseAuthBackend(AuthBackend):
    """Production backend backed by the real Supabase client."""

    def __init__(self, url: str, key: str):
        self._client = create_client(url, key)

    @staticmethod
    def _to_user(raw) -> User:
        return User(
            id=str(raw.get("id")),
            email=raw.get("email", ""),
            metadata=raw.get("user_metadata") or raw.get("app_metadata") or {},
        )

    def sign_up(self, email: str, password: str) -> AuthResult:
        res = self._client.auth.sign_up({"email": email, "password": password})
        user = self._to_user(res.user)
        session = res.session
        if session is None:
            # Email confirmation may be required; issue a token-less marker
            # in that case by failing — caller decides.
            raise SupabaseError("Please check your email to confirm", 400)
        return AuthResult(
            user=user,
            access_token=session.access_token,
            refresh_token=session.refresh_token,
        )

    def login(self, email: str, password: str) -> AuthResult:
        res = self._client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        user = self._to_user(res.user)
        session = res.session
        return AuthResult(
            user=user,
            access_token=session.access_token,
            refresh_token=session.refresh_token,
        )

    def logout(self, access_token: str) -> None:
        # For stateless JWT auth we send the token as the bearer; supabase-py
        # expects it in scope. We pass it explicitly to revoke.
        self._client.postgrest.auth(access_token)
        self._client.auth.sign_out()

    def get_user(self, access_token: str) -> Optional[User]:
        try:
            res = self._client.auth.get_user(access_token)
            raw = res.user
            return self._to_user(raw)
        except Exception:
            return None


class MockAuthBackend(AuthBackend):
    """In-memory fake so the API is testable without a live Supabase."""

    def __init__(self):
        self._users = {}      # email -> {id, password, metadata}
        self._tokens = {}     # token -> email
        self._seq = 0

    def _new_token(self):
        import uuid
        return uuid.uuid4().hex

    def sign_up(self, email: str, password: str) -> AuthResult:
        email = email.lower()
        if email in self._users:
            raise SupabaseError("User already registered", 400)
        self._seq += 1
        uid = f"mock-user-{self._seq}"
        self._users[email] = {
            "id": uid,
            "password": password,
            "metadata": {"role": "authenticated"},
        }
        return self.login(email, password)

    def login(self, email: str, password: str) -> AuthResult:
        email = email.lower()
        rec = self._users.get(email)
        if not rec or rec["password"] != password:
            raise SupabaseError("Invalid login credentials", 401)
        access_token = self._new_token()
        refresh_token = self._new_token()
        self._tokens[access_token] = email
        user = User(rec["id"], email, rec["metadata"])
        return AuthResult(user, access_token, refresh_token)

    def logout(self, access_token: str) -> None:
        self._tokens.pop(access_token, None)

    def get_user(self, access_token: str) -> Optional[User]:
        email = self._tokens.get(access_token)
        if not email:
            return None
        rec = self._users[email]
        return User(rec["id"], email, rec["metadata"])


def create_auth_backend():
    """Factory: real Supabase when credentials exist, mock otherwise.

    With SUPABASE_URL + SUPABASE_KEY set the production client is used.
    When they are absent (e.g. running the test-suite locally) a mock
    backend is used so everything is still verifiable.
    """
    if Settings.SUPABASE_URL and Settings.SUPABASE_KEY:
        return SupabaseAuthBackend(Settings.SUPABASE_URL, Settings.SUPABASE_KEY)
    return MockAuthBackend()
