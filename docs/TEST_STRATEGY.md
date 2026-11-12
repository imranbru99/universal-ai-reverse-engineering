# TEST STRATEGY

## Layers

1. **Unit** — models, URL/SSRF guards, fingerprinting, claim schema, generators
2. **Integration** — API + Postgres + Redis + MinIO (Compose)
3. **Worker** — stage machine resume, exploration against demo-target
4. **E2E** — signup/login → analyze → review → generate → export
5. **Security** — cross-tenant denial, out-of-scope block, upload limits
6. **A11y** — axe on primary SaaS views (planned expansion)

## Coverage honesty

Report coverage of *observed* states/transitions within declared scope. Never claim 100% of an external app without a complete inventory.

## Commands

See README. CI should run `pytest` and web tests on every PR.
