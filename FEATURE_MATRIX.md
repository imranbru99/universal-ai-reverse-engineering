# FEATURE MATRIX — REVERSEFORGE AI

Legend: **I** implemented · **T** tested · **P** partial · **B** blocked · **PL** planned

Last updated: 2026-11-13 (vertical slice verified)

| ID | Feature | Status | Evidence |
|----|---------|--------|----------|
| F01 | Multi-tenant orgs, memberships, roles | I/T | Seed + API; cross-tenant 404 in acceptance |
| F02 | Registration / login | I/T | `/auth/register`, `/auth/login`; demo user |
| F03 | Project wizard + authorization scope | I/T | Web wizard + create project API |
| F04 | Evidence ingestion + provenance | P | Stage C checkpoint; upload API still thin |
| F05 | Playwright exploration MVP | I/T | Worker explorer vs demo-target; 8 states observed |
| F06 | Screen state + transition graph | I/T | 8 states / 44 transitions persisted |
| F07 | Inference claims + review queue | I/T | Claims API + approve in acceptance |
| F08 | Domain / API proposals | I/T | Heuristic Book/Cart/User entities |
| F09 | Generation (Next/FastAPI/PG) | I/T | `demo_bookstore_export.zip` produced |
| F10 | Generated app tests + visual diff | P | Generator includes smoke tests; visual diff stub |
| F11 | Durable stage machine + resume | P | Stage checkpoints written; restart resume unit coverage pending |
| F12 | Tenant isolation enforcement | I/T | Cross-tenant run GET → 404 |
| F13 | SSRF / out-of-scope block | I/T | URL guard unit tests + integration private IP |
| F14 | Billing administration | PL | — |
| F15 | Mobile APK/iOS static analysis | PL | — |
| F16 | Repository Tree-sitter analysis | PL | — |
| F17 | Kubernetes production manifests | P | Skeleton under `infra/k8s` |
| F18 | Full OpenTelemetry dashboards | PL | Not wired |
| F19 | Additional stack adapters | PL | After first target solid |
| F20 | Bundled demo E2E acceptance | I/T | `scripts/acceptance_demo.py` → `ACCEPTANCE_OK` |
| F21 | S3/MinIO object storage | B/P | Registry pull blocked; local filesystem artifacts used |

## Explicitly unavailable / not claimed

- Automatic CAPTCHA solving or anti-bot evasion
- Discovery of unauthorized credentials or private schemas
- 100% coverage claims for arbitrary third-party apps
- Byte-identical proprietary UI asset reproduction
- Hosted MinIO in local Compose (image pull denied in this environment)

## Acceptance verification (this session)

```
states=8 transitions=44 claims=3 entities=3
export=demo_bookstore_export.zip
cross_tenant=404
ACCEPTANCE_OK
```
