# DATA MODEL

Core entities (PostgreSQL). All tenant resources include `organization_id` unless global.

## Identity

- `users` — id, email, password_hash, is_active, created_at
- `organizations` — id, name, slug, kill_switch, created_at
- `memberships` — user_id, organization_id, role (owner|admin|analyst|viewer)
- `roles` / `permissions` — optional fine-grained map (MVP uses enum roles)

## Projects & scope

- `projects` — org, name, description, status
- `target_applications` — project, base_url, app_type, name
- `target_versions` — target, label, captured_at
- `authorization_scopes` — allowlist_domains[], path_prefixes[], max_depth, max_pages, max_minutes, allow_authenticated, notes, signed_by
- `credentials_references` — project, label, role_hint, secret_ref (encrypted), never plaintext API responses

## Evidence & analysis

- `evidence_items` — project, kind, storage_key, sha256, source, metadata
- `analysis_runs` — project, status, current_stage, stage_state JSON, budgets
- `analysis_jobs` — run, job_type, celery_task_id, status, attempts

## Graph

- `screen_states` — run, fingerprint, url, title, auth_state, role, viewport, components JSON, screenshot_key, confidence, completeness
- `screen_components` — state, component_type, name, props JSON
- `transitions` — run, from_state, to_state, trigger, inputs JSON, preconditions JSON, evidence
- `workflows` — run, name, entry_state, graph JSON

## Inference & generation

- `observed_api_calls`, `proposed_api_endpoints`
- `domain_entities`, `domain_fields`, `relationships`
- `design_tokens`, `specifications`
- `inference_claims`, `claim_evidence`, `review_decisions`
- `generation_plans`, `generation_tasks`, `generated_files`, `code_artifacts`
- `test_cases`, `test_runs`, `visual_comparisons`
- `security_findings`, `approvals`, `exports`
- `usage_events`, `subscriptions`, `audit_events`

See SQLAlchemy models in `apps/api/app/models/` and Alembic migrations for authoritative schema.
