# ADR 0001 — Platform Foundation

- Status: Accepted
- Date: 2026-11-13

## Context

REVERSEFORGE AI must deliver an authorized analysis → specification → independent reconstruction SaaS. The repository started empty. We need a foundation that is secure, multi-tenant, durable under worker restarts, and capable of a vertical slice against a bundled demo application.

## Decision

1. **Monorepo** with `apps/web` (Next.js/TS), `apps/api` (FastAPI/Python), `workers` (Celery), shared packages, Compose-first local infra.
2. **PostgreSQL** as system of record; **Redis** for Celery broker/result; **MinIO** for S3-compatible artifacts.
3. **Playwright** for scoped web exploration; state graph persistence for screens/transitions.
4. **Durable pipeline stages A–O** with DB checkpoints; resume after worker restart.
5. **First generation target only:** Next.js + FastAPI + PostgreSQL. Other stacks are adapter stubs.
6. **Claim provenance** stored relationally (`inference_claims`, `claim_evidence`, `review_decisions`).
7. **Security defaults:** org RBAC, scope allowlists, SSRF private-IP blocks, audit events, kill switch.
8. **Bundled `apps/demo-target`** bookstore-style app for deterministic demos without third-party dependency.

## Consequences

- Faster local iteration via Docker Compose; production path documented under `infra/k8s`.
- AI features degrade gracefully to deterministic heuristics when no API key is configured.
- Scope intentionally excludes mobile/binary deep analysis until web vertical slice meets acceptance criteria.

## Alternatives considered

- Polyrepo services — rejected for early velocity.
- Temporal instead of Celery — deferred; Celery + DB stage state is sufficient for MVP durability.
- Only TypeScript backend — rejected; Python ecosystem better fits Playwright orchestration, parsing, and ML tooling.
