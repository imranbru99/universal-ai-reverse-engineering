# IMPLEMENTATION ROADMAP

## Milestone 0 — Bootstrap (this session start)

- [x] Inspect environment (Node, Docker present; Python installed as needed)
- [x] ADR, FEATURE_MATRIX, THREAT_MODEL, AGENTS, ARCHITECTURE
- [x] Monorepo scaffold + Compose + `.env.example`
- [x] Initial migrations + seed

## Milestone 1 — Vertical slice (acceptance path)

1. [x] Auth + org + project + scope
2. [x] Demo-target app live on Compose network
3. [x] Analysis run → Playwright explore → states/transitions
4. [x] Inference claims + domain proposals + review approve
5. [x] Generate independent app ZIP
6. [x] Tenant isolation + SSRF/scope tests green
7. [ ] Worker restart resume automated test (checkpoints exist; dedicated resume test pending)

## Milestone 2 — Hardening

- Full rate limits, retention jobs, richer audit UI
- Prompt-injection test corpus
- Visual diff tolerances + coverage metrics dashboard
- OpenTelemetry exporters

## Milestone 3 — Evidence breadth

- HAR/OpenAPI ingestion depth
- Repo Tree-sitter analyzer
- Design-token editor + component library export

## Milestone 4 — Additional adapters

- Laravel + Filament, Django, React Native, Flutter (only after Milestone 1 verified)

## Prioritized task list (session)

| P | Task |
|---|------|
| P0 | Compose stack runnable |
| P0 | API models/migrations/auth |
| P0 | Demo target + seed |
| P0 | Explorer worker + state graph |
| P0 | Web login + project + workspace |
| P0 | Generation + export |
| P0 | Security tests (tenant, SSRF, scope) |
| P1 | Review UI polish |
| P1 | E2E Playwright for SaaS |
| P2 | K8s manifests expansion |
| P2 | Billing stubs |
