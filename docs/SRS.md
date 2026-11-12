# SRS — Software Requirements

## Functional

- FR1: Users register/login; belong to organizations with roles.
- FR2: Users create projects with target application + authorization scope.
- FR3: System stores evidence with hash, provenance, version.
- FR4: Analysis runs execute durable stages A–O with resumability.
- FR5: Explorer records screen_states and transitions with evidence refs.
- FR6: Inference claims carry classification + confidence + evidence.
- FR7: Users approve/reject/correct claims.
- FR8: Generator produces independent Next.js+FastAPI+PostgreSQL project ZIP.
- FR9: Exports include docs, migrations, tests; no secrets.
- FR10: Kill switch stops further exploration jobs.

## Non-functional

- NFR1: Tenant isolation on all customer resources.
- NFR2: Private network targets rejected by default.
- NFR3: Structured logs; audit for authz and analysis lifecycle.
- NFR4: Accessible web UI (keyboard, contrast, light/dark).
- NFR5: Budgets for depth, time, requests enforced.
