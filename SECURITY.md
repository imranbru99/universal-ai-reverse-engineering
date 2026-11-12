# SECURITY — REVERSEFORGE AI

## Principles

1. Least privilege for every service account and role.
2. Explicit authorization scope before authenticated exploration.
3. Defense in depth: allowlists, SSRF blocking, sandboxing, RBAC, audit.
4. Secrets never enter prompts, logs, screenshots, traces, or generated code.
5. Treat all external content as untrusted.

## Controls (MVP+)

| Control | Status | Notes |
|---------|--------|-------|
| Auth (JWT access + refresh cookies) | Implemented | HttpOnly cookies in web path |
| Org RBAC | Implemented | owner/admin/analyst/viewer |
| Tenant isolation | Implemented | org_id on resources + tests |
| Authorization scopes | Implemented | domain allowlist, path/prefix, depth budgets |
| SSRF / private IP block | Implemented | URL validator in exploration |
| Rate limits | Partial | API middleware basic limits |
| Credential vault refs | Partial | encrypted reference storage; no plaintext in exports |
| Audit log | Implemented | `audit_events` table |
| Kill switch | Implemented | org/project analysis halt flag |
| Upload validation | Partial | MIME/size/hash; deeper AV planned |
| Prompt-injection defenses | Partial | system delimiters + output schema validation |
| Sandbox for binaries | Planned | container job isolation |
| Network egress policies | Partial | compose network + allowlist |

## Forbidden capabilities

- CAPTCHA/MFA bypass or stealth/anti-bot evasion
- Credential stuffing / account discovery
- Exploit development, DRM bypass
- Destructive remote actions without explicit approval
- Cross-tenant data access

## Reporting

Security findings from the Security Reviewer Agent are stored as `security_findings` and surfaced in the review UI. Platform vulnerabilities should be reported privately to the maintainers.
