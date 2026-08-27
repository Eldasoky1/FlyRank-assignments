"""Geo enrichment with A->B fallback.

Rule per the brief: degrade gracefully, never fail. Try provider A (ip-api.com),
on any failure/timeout/error or non-success fall back to provider B (ipapi.co).
If both fail, return {}. The caller must tolerate empty geo.
"""

import time

import httpx

def _parse_ip_api(data):
    if not isinstance(data, dict) or data.get("status") != "success":
        raise ValueError("bad ip-api response")
    return {
        "provider": "ip-api",
        "country": data.get("country"),
        "country_code": data.get("countryCode"),
        "region": data.get("regionName"),
        "city": data.get("city"),
        "lat": data.get("lat"),
        "lon": data.get("lon"),
    }


def _parse_ipapi_co(data):
    if not isinstance(data, dict) or data.get("error"):
        raise ValueError("bad ipapi.co response")
    return {
        "provider": "ipapi.co",
        "country": data.get("country_name"),
        "country_code": data.get("country"),
        "region": data.get("region"),
        "city": data.get("city"),
        "lat": data.get("latitude"),
        "lon": data.get("longitude"),
    }


PROVIDERS = (
    # (name, url_builder, parser)
    ("ip-api", lambda ip: f"http://ip-api.com/json/{ip}", _parse_ip_api),
    ("ipapi.co", lambda ip: f"https://ipapi.co/{ip}/json/", _parse_ipapi_co),
)


class GeoResolver:
    def __init__(self, timeout=2.0, providers=PROVIDERS):
        self.timeout = timeout
        self.providers = providers

    def resolve(self, ip) -> dict:
        """Return geo dict from provider A, falling back to B, else {}."""
        if not ip or ip in ("127.0.0.1", "::1", "localhost"):
            # local/loopback: simulate a stable result so demos are testable
            return {
                "provider": "ip-api",
                "country": "Local",
                "country_code": "LOCAL",
                "region": None,
                "city": None,
            }
        for _, url_builder, parser in self.providers:
            try:
                resp = httpx.get(url_builder(ip), timeout=self.timeout)
                resp.raise_for_status()
                return parser(resp.json())
            except Exception:  # noqa: BLE001 - fall through to next provider
                continue
        return {}


class FakeGeoResolver(GeoResolver):
    """Deterministic resolver for offline tests / demo."""

    def resolve(self, ip):
        if not ip or ip in ("127.0.0.1", "::1"):
            return {"provider": "ip-api", "country": "Local", "country_code": "LOCAL"}
        return {
            "provider": "ip-api",
            "country": "Egypt",
            "country_code": "EG",
            "region": "Cairo",
            "city": "Cairo",
        }
