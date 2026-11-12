# ARCHITECTURE — REVERSEFORGE AI

## Goals

Build a multi-tenant SaaS that turns **authorized evidence** into validated specifications and an **independent** reconstructed application, with full provenance and human review gates.

## High-level topology

```
┌────────────┐     ┌────────────┐     ┌──────────────────────────┐
│  Next.js   │────▶│  FastAPI   │────▶│ PostgreSQL (tenant data) │
│  apps/web  │     │  apps/api  │     └──────────────────────────┘
└────────────┘     └─────┬──────┘
                         │ enqueue
                         ▼
                  ┌──────────────┐     ┌─────────────┐
                  │ Redis/Celery │────▶│   workers/  │
                  └──────────────┘     └──────┬──────┘
                                              │
                     ┌────────────────────────┼────────────────────────┐
                     ▼                        ▼                        ▼
              Playwright explore        AI structured           Object storage
              (scoped browser)          extraction              (S3/MinIO)
```

## Bounded contexts

1. **Identity & tenancy** — users, orgs, memberships, RBAC, audit.
2. **Authorization & scope** — target apps, allowlists, budgets, credentials refs.
3. **Evidence** — uploads, hashes, provenance, versions.
4. **Exploration** — screen states, transitions, workflows, traces.
5. **Inference** — claims, domain/API/design proposals, review decisions.
6. **Generation** — plans, tasks, artifacts, exports, visual comparisons.
7. **Billing & usage** — subscriptions, usage events (stub initially).

## Pipeline stages (durable)

| Stage | Name | Gate |
|-------|------|------|
| A | Intake & validation | Evidence checksum + type OK |
| B | Authorization/scope | Signed scope present |
| C | Evidence extraction | Artifacts stored |
| D | Screen/workflow graph | States + transitions persisted |
| E | Domain & API modeling | Claims created |
| F | Confidence & gaps | Gap report |
| G | Human review | Critical claims reviewed |
| H | Implementation planning | Plan approved |
| I–K | Code generation | Files validated |
| L–N | QA / visual / security | Thresholds met or waived |
| O | Packaging & export | ZIP + manifests |

Workers checkpoint after each stage. Restart resumes from last completed stage.

## State graph model

- **Node (`screen_states`)**: URL/route, auth/role, viewport, components, messages, screenshot/DOM refs, confidence, completeness.
- **Edge (`transitions`)**: trigger, inputs, preconditions, expected effects, evidence refs, error cases.
- Canonical fingerprints prevent infinite loops; BFS + risk-aware priority; budgets on depth/time/requests/tokens.

## AI provider abstraction

`packages/ai` exposes `CompletionClient` with structured-output validation. Hosted and local providers plug in. Unchecked code/shell from models is never executed.

## First reconstruction target

**Next.js + FastAPI + PostgreSQL** via `packages/generation` adapter. Additional stacks (Laravel, Django, RN, Flutter) are adapter slots only until the first target meets acceptance criteria.

## Tenancy & security

- Every row carrying customer data includes `organization_id`.
- API layer enforces membership + permission checks.
- Cross-tenant IDs return 404/403 (no existence leak where practical).
- Egress from workers is allowlist-constrained; private IP ranges blocked (SSRF defense).

## Observability

Structured JSON logs, OpenTelemetry traces/metrics (wiring in `infra`), audit_events for security-relevant actions.
