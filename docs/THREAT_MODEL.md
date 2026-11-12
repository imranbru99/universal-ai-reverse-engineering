# THREAT MODEL — REVERSEFORGE AI

## Assets

- Customer evidence (screenshots, HAR, source zips, credentials references)
- Analysis artifacts (DOM dumps, traces, inferred models)
- Generated independent code and exports
- Tenant identity and RBAC bindings
- Platform secrets (DB, Redis, object storage, AI keys)

## Actors

- Legitimate tenant users (owner/admin/analyst/viewer)
- Malicious tenant (cross-tenant probing, prompt injection via uploads)
- External attackers (API abuse, SSRF via crawl URL)
- Compromised worker process
- AI provider (untrusted output)

## Key threats & mitigations

| ID | Threat | Impact | Mitigation |
|----|--------|--------|------------|
| T01 | SSRF via target URL | Internal network scan | Block private/link-local IPs; scheme allowlist; DNS rebinding checks |
| T02 | Scope escape crawl | Unauthorized data access | Domain/path allowlist; skip log; kill switch |
| T03 | Cross-tenant IDOR | Data breach | org_id filters; membership checks; tests |
| T04 | Credential leakage | Account takeover | Secret refs only; redaction filters; no creds in AI prompts |
| T05 | Prompt injection in pages/docs | Unsafe generation / tool abuse | Structured outputs; deny shell exec from model; human gates |
| T06 | Malicious upload | RCE in parser | Type/size limits; sandbox; no native deserialize of untrusted pickle |
| T07 | Queue poison / replay | Unauthorized jobs | Signed job payloads scoped to org; authz re-check in worker |
| T08 | Supply chain deps | Compromised builds | Pin versions; license/vuln scan in CI (planned) |
| T09 | Over-collection | Privacy violation | Retention policies; minimize PII fields |
| T10 | Destructive remote actions | Customer harm | Default deny; approval records |

## Trust boundaries

1. Browser ↔ Web UI (CSP, cookies)
2. Web UI ↔ API (authn/z)
3. API ↔ DB/Redis/S3
4. Worker ↔ Target application (egress allowlist)
5. Worker ↔ AI provider (no secrets in prompts)

## Residual risks

- DNS rebinding races require continuous hardening.
- Visual analysis may overfit brand cues; generation must substitute independent assets.
- Local model deployments share host risk with workers — isolate in production.
