# Tenant isolation verification

Automated HTTP checks live in `tests/integration/test_api_flow.py` (run against a live Compose stack).

Expected:

1. User A cannot GET User B analysis run (404).
2. User A cannot download User B export (404).
3. Out-of-scope URL host rejected at project create (400).
