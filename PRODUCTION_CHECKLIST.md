# DotMac Production Checklist

This checklist is meant to be filled per environment/tenant. Provide the values in the "Required Inputs" section before starting.

## Required Inputs (fill in)
- Environment name (e.g., prod, staging):
- Tenant name/slug:
- API domain (e.g., api.example.com):
- Admin UI domain (e.g., app.example.com):
- TLS certificate paths/ARNs (API/Admin):
- Database host/port/name/user:
- Redis host/port/db:
- Object storage endpoint/bucket:
- Vault/OpenBao URL:
- OTEL endpoint (gRPC + HTTP):
- Alertmanager/Prometheus/Grafana URLs:
- Compose project name or Helm release/namespace:

## Pre-Flight
- [ ] All secrets are set and **not** using defaults (`SECRET_KEY`, `AUTH__JWT_SECRET_KEY`, `NEXTAUTH_SECRET`).
- [ ] Database credentials are unique per tenant/environment.
- [ ] Redis credentials are unique per tenant/environment.
- [ ] Object storage access key/secret are unique and rotated.
- [ ] Vault/OpenBao token uses least privilege and is rotated.
- [ ] CORS origins match the Admin UI domain(s).
- [ ] Feature flags reflect intended launch scope.

## Domain + TLS
- [ ] DNS records created for API and Admin UI domains.
- [ ] TLS certificates issued and stored (API/Admin).
- [ ] Nginx `server_name` updated for API domain.
- [ ] TLS paths in Nginx config updated to correct cert/key/chain.
- [ ] HSTS and CSP reviewed for production requirements.

## Application Configuration
- [ ] `.env.production` (or env vars) populated from Required Inputs.
- [ ] `DATABASE_URL` resolves correctly from `DATABASE__*` entries.
- [ ] Redis URLs set for sessions and Celery broker/result backend.
- [ ] `REQUIRE_REDIS_SESSIONS=true` verified.
- [ ] Observability endpoints are set and reachable.
- [ ] `ENABLE_METRICS` and `ENABLE_TRACING` set as intended.
- [ ] Debug logging is disabled (`LOG_LEVEL=info` or higher).

## Infrastructure (Compose Path)
- [ ] `docker-compose.infra.yml` services are healthy.
- [ ] `docker-compose.base.yml` started with `--env-file .env.production`.
- [ ] `docker-compose.prod.yml` started with the **same** env file.
- [ ] `platform-backend` and `platform-worker` are healthy.
- [ ] `platform-worker` has **no** dev defaults for Redis/MinIO/Vault.

## Infrastructure (Kubernetes/Helm Path)
- [ ] Namespace created for tenant.
- [ ] Secrets created for DB/Redis/Object storage/Vault.
- [ ] Helm values updated for domains, TLS, resources, and images.
- [ ] Release installed/updated and pods ready.
- [ ] Migrations executed via Job or hook.

## Database + Migrations
- [ ] Backup snapshot taken before migration.
- [ ] `alembic upgrade head` executed successfully.
- [ ] Post-migration smoke queries run.

## Web + API Verification
- [ ] `/health` returns 200 on API domain.
- [ ] `/metrics` is reachable from allowed IPs only.
- [ ] Auth endpoints enforce rate limits.
- [ ] Admin UI loads and can authenticate.
- [ ] Sample tenant login succeeds.

## Observability
- [ ] Logs shipped to expected sink with request IDs.
- [ ] Metrics appear in Prometheus/Grafana.
- [ ] Traces appear in OTEL backend.
- [ ] Alertmanager receives test alert.

## Security
- [ ] CSP reviewed and tightened for production.
- [ ] No `unsafe-inline`/`unsafe-eval` unless required.
- [ ] Session storage persisted and secure cookie flags verified.
- [ ] RBAC roles tested for tenant/admin/partner.

## Data + Storage
- [ ] Object storage bucket exists and lifecycle policies applied.
- [ ] Upload/download flows validated.
- [ ] Backups scheduled for DB and object storage.

## Background Jobs
- [ ] Celery queues configured and visible.
- [ ] Worker concurrency tuned for expected load.
- [ ] Scheduled jobs verified (if any).

## Rollout + Monitoring
- [ ] Load test critical endpoints.
- [ ] 5xx/latency alerts configured.
- [ ] Runbook documented for rollback and incident response.
- [ ] Stakeholders notified and change window approved.

## Post-Deploy
- [ ] Verify partner/tenant admin flows.
- [ ] Audit logs are being recorded.
- [ ] Billing/analytics flags match launch scope.
- [ ] Document any deviations from this checklist.
