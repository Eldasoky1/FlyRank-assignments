"""Seed script: idempotent metering demo + a pro customer with usage.

Run: `python seed.py`
"""

from metering import MeteringService, MeteringStore
from plans import USAGE_AI_TOKENS, USAGE_API_CALLS

store = MeteringStore(":memory:")
service = MeteringService(store)

service.store.upsert_customer("customer_demo", plan="pro", active=1)

rk = service.record_usage("customer_demo", USAGE_API_CALLS, "seed-apicall-1", quantity=1, cost_cents=1)
print("api call recorded:", rk)

rk2 = service.record_usage(
    "customer_demo", USAGE_AI_TOKENS, "seed-gen-123", quantity=1500, cost_cents=1
)
print("ai tokens recorded:", rk2)

print("summary:", service.usage_summary("customer_demo"))
