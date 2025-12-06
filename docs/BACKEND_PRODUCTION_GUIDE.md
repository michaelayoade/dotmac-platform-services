# Backend Production Guide

Canonical steps for deploying the DotMac backend in production, per tenant. Two supported paths exist today:
- **Docker Compose** for single-host or small cluster rollouts.
- **Kubernetes/Helm** for cluster-native, per-namespace isolation.

## Inputs and prerequisites
- Pick an environment template: `.env.production.example` (general production) or `.env.example` (development baseline), then copy to the file you will pass via `--env-file`.
- Compose files:
  - `docker-compose.infra.yml` – databases, Redis, MinIO, observability, NetBox, OpenBao.
  - `docker-compose.base.yml` – platform API and admin UI.
  - `docker-compose.prod.yml` – Celery worker.
- Docker/Helm installed, access to PostgreSQL/Redis/MinIO endpoints, TLS certificates, and DNS entries for your chosen hostnames.

> Note: An ISP-specific compose file is not shipped in this repository. The supported compose path is the platform stack described below.

> Upgrade note: If you have existing deployments, update your `.env` to use `STORAGE__ENDPOINT/ACCESS_KEY/SECRET_KEY/BUCKET`, `AUTH__JWT_SECRET_KEY`, and `VAULT__URL=http://dotmac-openbao:8200` (or your own endpoint) so the compose files pick up the correct values instead of the old defaults.

## Compose path (single host or PoC)
The helper script orchestrates the compose stacks and performs health checks:
```bash
# Start shared infra only
./scripts/infra.sh infra start

# Start the platform stack (expects dotmac-network to exist)
./scripts/infra.sh platform start
```

> Network note: `docker-compose.base.yml` and `docker-compose.prod.yml` will create the `dotmac-network` bridge automatically if it does not exist. The infra stack reuses the same name so services share a network without manual creation.

Manual steps if you prefer explicit control:
```bash
# 1) Start infra (creates dotmac-network)
docker compose -f docker-compose.infra.yml up -d

# 2) Start API + admin UI with your production env file
docker compose -f docker-compose.base.yml --env-file .env.production up -d platform-backend platform-frontend

# 3) Run database migrations
docker compose -f docker-compose.base.yml --env-file .env.production exec platform-backend poetry run alembic upgrade head

# 4) Start background workers
docker compose -f docker-compose.prod.yml --env-file .env.production up -d platform-worker

# 5) Validate
docker compose -f docker-compose.base.yml ps
curl http://localhost:${PLATFORM_BACKEND_PORT:-8001}/health
```

> Tip: set `COMPOSE_PROJECT_NAME` per tenant to avoid container-name collisions, and override `PLATFORM_BACKEND_PORT`/`PLATFORM_FRONTEND_PORT` for parallel stacks.

## Kubernetes/Helm path (per-namespace tenants)
The `KubernetesAdapter` (`src/dotmac/platform/deployment/adapters/kubernetes.py`) expects a Helm chart and values that describe each tenant. Provide:
- Image repository/tag for the backend and worker.
- External services: PostgreSQL, Redis, object storage (MinIO/S3), Vault/OpenBao endpoint and token.
- Ingress hosts for API and admin UI, TLS secrets, and OTLP endpoints.
- Resource requests/limits and storage class preferences.

Typical flow:
```bash
# One namespace/release per tenant
kubectl create namespace tenant-a
helm upgrade --install tenant-a-platform <your-chart> \
  --namespace tenant-a \
  --version <chart-version> \
  -f values/tenant-a.yaml
```
After rollout, run migrations (Job or `helm test` hook), then verify `/health` and `/metrics` on the exposed service endpoints.

## Per-tenant rollout checklist
### If using Compose
- [ ] Create an env file per tenant (`.env.production`, `.env.tenant-a`, etc.) with isolated DB/Redis/MinIO credentials.
- [ ] Ensure `docker compose -f docker-compose.infra.yml up -d` is running or point app env vars to managed services.
- [ ] Start the tenant stack with a unique `COMPOSE_PROJECT_NAME` and port overrides.
- [ ] Run `poetry run alembic upgrade head` inside `platform-backend` for that tenant’s database.
- [ ] Start `platform-worker` for background tasks.
- [ ] Smoke-test `/health`, `/docs`, and a sample login for the tenant domain.

### If using Kubernetes/Helm
- [ ] Create a namespace per tenant and secrets for DB/Redis/object storage credentials.
- [ ] Prepare Helm values with tenant-specific hostnames, TLS secrets, and resource limits.
- [ ] `helm upgrade --install` the tenant release and wait for readiness.
- [ ] Execute migrations (Helm hook/Job) and validate `/health` + `/metrics`.
- [ ] Register the tenant in the control plane if you automate onboarding via the deployment service.
