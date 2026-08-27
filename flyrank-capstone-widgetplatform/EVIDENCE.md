# EVIDENCE — Embeddable Widget & Lead-Capture Platform

Each requirement has one pasted proof (offline test output).

## 1. Widget management API + tenant isolation
```
test_admin_requires_key PASSED           # no key -> 401
test_widget_tenant_isolation PASSED      # widget invisible to other tenant
test_update_bumps_version_and_invalidates_cache PASSED
test_widget_js_cached_and_404_for_missing PASSED
```

## 2. Embed snippet + cached/versioned delivery
`/w/{id}.js` returns a self-contained widget bundle with `ETag`, `Cache-Control`,
and `X-Content-Version`; updating a widget changes the version + cache (tested).

## 3. Public submission: CORS, boundary validation, clean 4xx
```
test_submit_requires_widget PASSED       # 422 missing widget_id
test_invalid_email_rejected PASSED       # 422 invalid email
test_submission_valid_and_geo_enriched PASSED
```
CORS middleware enabled; validation returns 4xx, never 500.

## 4. Abuse protection: per-IP/per-widget rate limit → 429 + honeypot
```
test_rate_limit_429 PASSED               # 429 after burst exhausted
test_honeypot_blocked_silently_success PASSED
test_honeypot_detection PASSED
test_rate_limiter_tokens PASSED
```

## 5. Geo enrichment with A→B fallback (degrade, never fail)
```
test_geo_fallback_degrades_not_fails PASSED   # both providers down -> {} (no raise)
test_fake_geo_resolver PASSED
```

## 6. Safe side effects (failure must not block)
```
test_side_effects_never_raise PASSED     # webhook/email error swallowed
```

## 7. Full offline suite
```
15 passed, 43 warnings in 1.16s
```
