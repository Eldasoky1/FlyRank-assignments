# EVIDENCE — Social Media Studio

Each requirement has one pasted proof (offline, mock transports).

## 1. Image variants (per-platform sizes)
```
test_make_variants_produces_platform_sizes PASSED   # 1080x1080 IG, 1600x900 X, real files
test_variant_key_is_content_addr PASSED            # content-addressed dedup
```
6 platform specs (FB 1200x630, X 1600x900, IG square 1080x1080, IG story 1080x1920, LinkedIn 1200x627, YT 1280x720).

## 2. Caption composer (+ per-platform limits)
```
test_compose_contains_hook_hashtags PASSED
test_compose_truncates_to_platform_limit PASSED    # X post <= 280 chars, ellipsis
test_caption_is_filled_and_platform_model PASSED
```

## 3. SocialPublisher with 2 adapters + idempotent publish
```
test_facebook_publish_is_idempotent PASSED   # 2nd send -> 'already_published', SAME external_id
test_twitter_publish_works PASSED
test_publisher_consistent_external_id_for_same_content PASSED
```

## 4. 429 / Retry-After backoff
```
test_rate_limit_429_backs_off_with_retry_after PASSED
```
Adapters honor the server's `retry_after` delay across bounded retries before raising `HTTPError(429)`.

## 5. Encrypted OAuth tokens
```
test_oauth_roundtrip PASSED
test_oauth_no_plaintext_and_tamper_detected PASSED   # blob has no plaintext token; tamper raises
```

## 6. Durable scheduler — survives crashes without double-posting
```
test_scheduler_enqueue_is_idempotent PASSED      # same post queued once
test_scheduler_crash_recovery_reclaims_stale_running PASSED
test_scheduler_no_double_post_across_publishes PASSED
test_scheduler_marks_failed_job PASSED
```

## 7. Signature-verified webhooks → status tracking
```
test_webhook_valid_signature_applies PASSED
test_webhook_rejects_bad_signature PASSED
test_webhook_rejects_stale_timestamp PASSED
```
API proof (real run):
```
webhook: {'ok': True, 'platform': 'twitter_card', 'job_id': '6f12fd76', 'status': 'delivered'}
final status: delivered
bad-sig status: 400
```

## 8. API end-to-end
```
test_api_publish_and_signed_webhook PASSED
```
compose → schedule → publish (`done`, external_id) → signed webhook → status `delivered`.

## 9. Full offline suite
```
20 passed, 16 warnings in 9.8s
```
No live platform calls or network required.
