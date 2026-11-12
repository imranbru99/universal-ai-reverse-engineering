# WORKFLOW ENGINE

## State graph exploration

1. Seed queue with entry URL(s) from scope.
2. Canonicalize URL (strip volatile query params configured per project).
3. Fingerprint = hash(canonical_url + auth_state + viewport_bucket + dominant landmarks).
4. Skip if fingerprint visited or budgets exhausted.
5. Capture screenshot, accessibility snapshot, interactive actions.
6. Enqueue safe transitions (links, buttons, forms with fixtures).
7. Record skipped/blocked paths with reason (`out_of_scope`, `dangerous`, `mfa_handoff`, `budget`).

## Prioritization

BFS primary; boost likely workflow edges (nav, primary CTA); deprioritize logout/delete.

## Durability

`analysis_runs.current_stage` + `stage_state` JSON checkpointed after each stage and periodically during D.
