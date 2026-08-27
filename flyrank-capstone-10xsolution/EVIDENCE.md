# EVIDENCE — CampaignBooster (10x Solution)

Each program concept + milestone has a pasted proof (offline).

## Concept 1 — Structured schema-validated output
```
test_goal_produces_validated_plan PASSED   # CampaignPlan, 5 channels
test_plan_channels_have_assets PASSED
test_provider_invalid_raises PASSED
```

## Concept 2 — Guardrail with rejection + explanation
```
test_guardrail_passes_valid_plan PASSED
test_guardrail_rejects_vague_plan PASSED   # ok=False with objective/audience reasons
```

## Concept 3 — Cost / budget accounting
```
test_budget_projection_totals PASSED
```
Real projection: `Total: $49.50`, grand_total_cents=4950 (integer-cents, no float drift).

## Concept 4 — Multi-stage pipeline (orchestration, retries, progress, cost, checklist)
```
test_pipeline_completes_all_stages PASSED   # 5 stages ran, cost > 0, report produced
test_pipeline_retries_then_fails_on_stage_error PASSED  # stage failed, retried, succeeded
test_checklist_build PASSED                  # checklist with ownership + status
test_pipeline_produces_report_deliverable PASSED
```

## Concept 5 — Report / artifact generation
Real API run:
```
status: completed  stages: ['plan','guardrail','budget','checklist','report']  cost_uc: 12
# CampaignBooster plan
**Objective:** launch a referral program for agencies
**Weeks:** 2
## Guardrail
PASS :: ok
## Budget
Total: $49.50
## Checklist
- [ ] facebook: hero (owner facebook)
- [ ] facebook: carousel (owner facebook)
- [ ] facebook: story (owner facebook)
... (15 items across facebook/instagram/linkedin/youtube/x)
```

## Concept 6 — Provider abstraction / pluggability
`PLAN_PROVIDER=mock` default; `gemini` path stubbed, invalid provider raises a clear error
(`test_provider_invalid_raises`).

## API end-to-end
```
test_api_full_flow PASSED        # submit -> 5 stages -> report with Objective
test_api_rejects_short_goal PASSED  # 422 on vague input
```

## Full offline suite
```
12 passed, 14 warnings in 1.65s
```

## All 5 milestones delivered (MILESTONES.md)
M1 plan · M2 guardrail · M3 budget · M4 pipeline · M5 deliverable+API — each mapped to a passing test.
