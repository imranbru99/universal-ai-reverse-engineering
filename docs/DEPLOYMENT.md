# DEPLOYMENT

## Local

```bash
cp .env.example .env
docker compose up --build
```

## Production (Kubernetes sketch)

Manifests under `infra/k8s/` provide Deployment/Service/Ingress templates for api, worker, web, plus external managed PostgreSQL/Redis/S3 recommendations.

Checklist:

- TLS termination
- Secrets via sealed-secrets / external secrets
- NetworkPolicies restricting worker egress to allowlisted CIDRs/domains
- HPA on api/worker
- Persistent volume only if required; prefer object storage
- Backup PostgreSQL; retention jobs for evidence
