# API SPEC (v1)

Base: `/api/v1` · Auth: `Authorization: Bearer <access_token>` or HttpOnly cookie.

## Auth

- `POST /auth/register` — create user + personal org
- `POST /auth/login` — access + refresh tokens
- `POST /auth/refresh`
- `GET /auth/me`

## Organizations & projects

- `GET /orgs`
- `POST /orgs`
- `GET /orgs/{org_id}/projects`
- `POST /orgs/{org_id}/projects` — name, target_url, scope
- `GET /projects/{project_id}`
- `POST /projects/{project_id}/scope`
- `POST /projects/{project_id}/kill-switch`

## Evidence & analysis

- `POST /projects/{project_id}/evidence` — multipart upload
- `POST /projects/{project_id}/analysis-runs`
- `GET /analysis-runs/{run_id}`
- `GET /analysis-runs/{run_id}/states`
- `GET /analysis-runs/{run_id}/transitions`
- `GET /analysis-runs/{run_id}/claims`
- `POST /claims/{claim_id}/review` — approve|reject|correct
- `POST /analysis-runs/{run_id}/generate`
- `GET /analysis-runs/{run_id}/export` — ZIP download

OpenAPI: served live at `/docs` and `/openapi.json`.
