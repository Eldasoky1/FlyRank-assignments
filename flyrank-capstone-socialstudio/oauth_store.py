"""Encrypted OAuth token store (Fernet).

Tokens are encrypted at rest with a key derived from an app secret via PBKDF2.
Uses cryptography's Fernet (authenticated encryption). In tests a fixed secret
is used and round-tripping is proven. Never store real tokens in plaintext.
"""

from __future__ import annotations

import base64
import hashlib
import os
import threading

from cryptography.fernet import Fernet


def _derive_key(secret: str) -> bytes:
    digest = hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), b"flyrank-social", 120_000)
    return base64.urlsafe_b64encode(digest)


class OAuthStore:
    def __init__(self, secret: str | None = None):
        self._fernet = Fernet(_derive_key(secret or os.getenv("OAUTH_SECRET", "dev-only-secret")))
        self._tokens = {}
        self._lock = threading.Lock()

    def save(self, platform: str, account: str, token: dict) -> None:
        payload = f"{platform}|{account}".encode("utf-8")
        blob = self._fernet.encrypt(payload + b"::" + _json(token).encode("utf-8"))
        with self._lock:
            self._tokens[(platform, account)] = blob

    def load(self, platform: str, account: str) -> dict | None:
        with self._lock:
            blob = self._tokens.get((platform, account))
        if not blob:
            return None
        raw = self._fernet.decrypt(blob)
        _, json_str = raw.split(b"::", 1)
        return _parse(json_str.decode("utf-8"))

    def has(self, platform: str, account: str) -> bool:
        return (platform, account) in self._tokens


def _json(obj: dict) -> str:
    import json

    return json.dumps(obj, sort_keys=True)


def _parse(s: str) -> dict:
    import json

    return json.loads(s)
