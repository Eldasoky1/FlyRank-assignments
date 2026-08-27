"""Abuse protection: token-bucket rate limiting + honeypot.

Per-IP and per-widget limits. Exceeding -> 429.
"""

import threading
import time


class RateLimiter:
    def __init__(self, rate_per_min, burst=None):
        self.rate = rate_per_min
        self.burst = burst or rate_per_min
        self._tokens = {}
        self._lock = threading.Lock()

    def allow(self, key) -> bool:
        now = time.monotonic()
        with self._lock:
            last, tokens = self._tokens.get(key, (now, self.burst))
            refill = (now - last) * (self.rate / 60.0)
            tokens = min(self.burst, tokens + refill)
            if tokens < 1:
                self._tokens[key] = (now, tokens)
                return False
            self._tokens[key] = (now, tokens - 1)
            return True


HONEYPOT_FIELD = "homepage"  # hidden field; bots fill it in


def is_honeypot_filled(form_data) -> bool:
    """Return True if the hidden honeypot field was filled (bots)."""
    val = form_data.get(HONEYPOT_FIELD)
    if isinstance(val, list):
        val = val[0] if val else ""
    return bool(val)


def validate_lead(data, limit_email=200):
    """Boundary validation for a lead payload. Returns (ok, reason)."""
    email = (data.get("email") or "").strip()
    if not email:
        return False, "email is required"
    if len(email) > limit_email:
        return False, "email too long"
    if "@" not in email or "." not in email.split("@")[-1]:
        return False, "invalid email"
    name = data.get("name") or ""
    if len(name) > 200:
        return False, "name too long"
    for key in ("email", "name"):
        if key in data and isinstance(data[key], (list, dict)):
            return False, f"{key} must be a string"
    return True, "ok"
