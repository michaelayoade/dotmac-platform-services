# Development SOP (DotMac)

Purpose: provide a repeatable process for changes to move from dev → staging → production with quality and security gates.

## Scope
Applies to backend, frontend, infrastructure, and data migrations in this repo.

## Roles (fill in)
- Developer:
- Reviewer:
- Release manager:

## Inputs (fill in)
- Target environment (dev/staging/prod):
- Change summary:
- Risk level (low/medium/high):
- Rollback plan:
- Related tickets/issue IDs:

## Stage 1: Local Development
- [ ] Reproduce the issue or implement the feature.
- [ ] Add or update tests for the change.
- [ ] Run relevant tests locally (unit/integration for affected modules).
- [ ] Update docs or runbooks if behavior changes.
- [ ] Confirm no debug settings are enabled.

## Stage 2: Pre-Review Checklist
- [ ] Code compiles/builds locally.
- [ ] Migrations reviewed for correctness and reversibility.
- [ ] Config changes documented (`.env.production.example` if needed).
- [ ] API changes documented (OpenAPI/README as needed).
- [ ] Security review: inputs validated, authz checked, secrets not logged.

## Stage 3: Code Review
- [ ] Reviewer validates correctness and tests.
- [ ] Reviewer verifies API/auth/security changes.
- [ ] Reviewer confirms migrations are safe and non-destructive.
- [ ] Changes approved for staging.

## Stage 4: Staging Release
- [ ] Deploy the release candidate to staging.
- [ ] Run migrations in staging.
- [ ] Smoke test critical flows (auth, billing, tenant, integrations).
- [ ] Verify metrics/logs/traces appear in observability stack.
- [ ] Confirm error rates and latency are within baseline.

## Stage 5: Production Readiness Gate
- [ ] Staging tests green.
- [ ] Rollback plan documented and validated.
- [ ] Change window approved.
- [ ] Production checklist reviewed and filled.
- [ ] Release artifacts tagged (Docker image tag/Helm chart version).

## Stage 6: Production Release
- [ ] Deploy the same artifact used in staging.
- [ ] Run migrations (if required).
- [ ] Validate `/health` and `/metrics`.
- [ ] Monitor logs/alerts for 30–60 minutes.

## Stage 7: Post-Release
- [ ] Confirm customer-facing flows.
- [ ] Capture any incidents or regressions.
- [ ] Update changelog/runbook with lessons learned.

## Optional: Fast Fix Path (Low Risk)
- [ ] Hotfix branch with minimal change.
- [ ] Targeted tests only.
- [ ] Deploy to staging, verify, then promote.
