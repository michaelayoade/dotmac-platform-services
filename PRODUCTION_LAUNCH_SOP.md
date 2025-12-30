# Production Launch SOP (SaaS Control Plane)

Purpose: formalize the steps and gates required to launch the DotMac platform as a SaaS control plane manager.

## 1) Scope + Launch Criteria (fill in)
- Launch date/window:
- Initial modules enabled (auth, tenants, billing, monitoring, partner, etc.):
- Target regions:
- Stop conditions (e.g., auth errors > 1% for 5 minutes):

## 2) Close Known Functional Gaps (required)
- [ ] Partner multi-tenant endpoints are either implemented or disabled behind feature flags.
- [ ] AWX provisioning is either fully implemented or disabled in production.
- [ ] Any placeholder logic that returns zeros/empty lists is documented or removed.

## 3) Security + Compliance Gate
- [ ] Secrets are unique and non-default (`SECRET_KEY`, `AUTH__JWT_SECRET_KEY`, `NEXTAUTH_SECRET`).
- [ ] CSP reviewed; remove `unsafe-inline`/`unsafe-eval` unless required.
- [ ] Rate limits tuned for auth and API endpoints.
- [ ] Session cookies are secure, HTTP-only, and SameSite as intended.
- [ ] RBAC tested for tenant/admin/partner roles.
- [ ] Audit logging enabled and verified.

## 4) Environment Separation
- [ ] Staging and production have separate DB/Redis/storage and credentials.
- [ ] Production data is not shared with staging.
- [ ] Access control to production is limited and audited.

## 5) Configuration Gate
- [ ] `.env.production` or Helm values populated with final domains and endpoints.
- [ ] CORS origins match Admin UI and API domains.
- [ ] Observability endpoints (OTEL/Prometheus/Grafana/Alertmanager) are reachable.
- [ ] Debug logging disabled in production.

## 6) Infrastructure Gate (Helm)
- [ ] TLS certificates issued and attached to API/Admin domains.
- [ ] Health checks validate `/health` and `/metrics`.
- [ ] Worker runs with the same env config as the API.
- [ ] Object storage bucket exists and lifecycle policies are applied.
 - [ ] Namespace created for the tenant/release.
 - [ ] Kubernetes secrets created for DB/Redis/storage/Vault credentials.
 - [ ] Helm values file includes image tags, resource requests/limits, and ingress hosts.

### Helm Commands (template)
```bash
# 1) Create namespace
kubectl create namespace <tenant-namespace>

# 2) Apply secrets (example: one secret per service)
kubectl -n <tenant-namespace> create secret generic dotmac-db \
  --from-literal=DATABASE_URL='postgresql://user:pass@host:5432/db'

kubectl -n <tenant-namespace> create secret generic dotmac-redis \
  --from-literal=REDIS_URL='redis://:pass@host:6379/0' \
  --from-literal=SESSION_REDIS_URL='redis://:pass@host:6379/1'

kubectl -n <tenant-namespace> create secret generic dotmac-storage \
  --from-literal=STORAGE__ENDPOINT='https://s3.example.com' \
  --from-literal=STORAGE__ACCESS_KEY='...' \
  --from-literal=STORAGE__SECRET_KEY='...' \
  --from-literal=STORAGE__BUCKET='dotmac'

kubectl -n <tenant-namespace> create secret generic dotmac-vault \
  --from-literal=VAULT__URL='https://vault.example.com' \
  --from-literal=VAULT__TOKEN='...'

# 3) Install/upgrade release
helm upgrade --install <release-name> <chart-path-or-repo> \
  --namespace <tenant-namespace> \
  -f values/<tenant>.yaml \
  --version <chart-version>

# 4) Run migrations (example Job hook name)
kubectl -n <tenant-namespace> create job --from=cronjob/<migration-cron> db-migrate-<release-name>

# 5) Validate
kubectl -n <tenant-namespace> get pods
kubectl -n <tenant-namespace> get ingress
```

## 7) Data + Migrations
- [ ] Backup snapshot taken before migration.
- [ ] `alembic upgrade head` executed successfully.
- [ ] Post-migration smoke queries validated.

## 8) Staging Final Rehearsal
- [ ] Deploy release candidate to staging with production-like config.
- [ ] Run migrations in staging.
- [ ] Smoke test core flows (auth, tenants, billing, jobs).
- [ ] Verify logs, metrics, and traces appear.

## 9) Production Release
- [ ] Deploy the exact artifact tested in staging.
- [ ] Run migrations.
- [ ] Verify `/health` and `/metrics`.
- [ ] Monitor error rate and latency for 30-60 minutes.
- [ ] Roll back if stop conditions are met.

## 10) Post-Launch Verification
- [ ] Validate customer-facing flows.
- [ ] Confirm alerting triggers and on-call routing.
- [ ] Document any deviations and open follow-up tasks.

## Release Pipeline Outline (Helm)
1) **Build**
   - Build backend and worker images.
   - Tag with immutable version (e.g., `vX.Y.Z` or commit SHA).
2) **Test**
   - Run unit + integration tests.
   - Run lint/type checks for frontend packages.
3) **Package**
   - Publish container images to registry.
   - Update Helm chart values to reference new tags.
4) **Staging Deploy**
   - `helm upgrade --install` staging with the new tags.
   - Run migrations and smoke tests.
5) **Promote**
   - Promote the same image tags to production values.
   - `helm upgrade --install` production.
6) **Monitor + Rollback**
   - Watch error rate/latency/alerts.
   - Roll back to the previous release if stop conditions are met.
