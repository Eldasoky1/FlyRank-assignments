# EVIDENCE — Usage Metering & Billing Engine

Each requirement has one pasted proof.

## 1. Idempotent usage metering (retries = one event)
Pasted test output:
```
tests/test_metering.py::test_meter_is_idempotent PASSED
tests/test_metering.py::test_record_usage_retry_does_not_double_count PASSED
```
Key logic: `metering.py` `UNIQUE(customer_id, idempotency_key, usage_type)` + `UsageReserved` on re-delivery; `total_used == 1` after 2 attempts.

## 2. Quota enforcement (429 vs 402, boundary-exact)
```
test_boundary_usage_allows_when_equal_not_exceeding PASSED   # 100/100 -> 429 on #101
test_ai_tokens_blocked_on_free_plan PASSED                   # 429 (limit 0)
test_inactive_pro_customer_gets_402 PASSED                   # 402 no active sub
test_active_pro_customer_uses_ai_tokens PASSED
```
`used == limit` is rejected; `QuotaExceeded`→429, `InsufficientPayment`→402.

## 3. AI-token cost rules (cached cheaper, reasoning=output, categories no cost)
```
test_cached_input_cheaper_than_uncached PASSED   # 10c vs 40c per 1M tokens
test_reasoning_tokens_billed_as_output PASSED    # reasoning == output == 120c/1M
test_categories_do_not_add_cost PASSED
test_zero_tokens_free PASSED
```
Costs returned as integer cents (`cost_cents`).

## 4. Stripe test mode, signature-verified, deduped webhooks
```
test_signature_verifies PASSED
test_forged_signature_rejected PASSED            # forged -> rejected
test_webhook_dedup_and_apply PASSED              # repeat -> deduped, applied once
test_forged_webhook_raises PASSED                # 400 on bad signature
```
`checkout.session.completed` provisions the `pro` plan; repeats are deduped via `stripe_events`.

## 5. Full offline suite
```
20 passed, 17 warnings in 0.88s
```
No real keys or network required.

## 6. Money as integer cents
- `plans.py` `price_per_unit_cents`
- `costing.py` returns `cost_cents` int
- `metering.py` stores `cost_cents INTEGER` and `quantity` (integers)
