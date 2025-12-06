# Quick Start Guide - DotMac FTTH Platform

**Last Updated**: 2025-11-04
**Status**: ✅ Production Ready

---

## 🚀 TL;DR

```bash
# Frontend (requires network access)
cd frontend
pnpm install
pnpm build:admin  # ✅ Platform Admin: 175 pages, 0 warnings

# Docker Compose - Platform (Admin + Backend)
cd ..

# Step 1: Check if external services are reachable
./scripts/check-external-services.sh

# Step 2: (Linux only) If host.docker.internal doesn't resolve, see DOCKER_COMPOSE_LINUX_COMPATIBILITY.md

# Step 3: Start the stack
docker compose -f docker-compose.base.yml up -d
# Platform backend: http://localhost:8001
# Platform frontend: http://localhost:3002
```

> Note: An ISP-specific Docker Compose stack is not included in this repository; the supported Compose path is the platform stack above.

> ⚠️ **External Dependencies Required**: The simplified compose files assume PostgreSQL (5432), Redis (6379), MinIO (9000), Vault (8200), and OTLP (4317) are reachable at `host.docker.internal`.
>
> - **Run pre-flight check**: `./scripts/check-external-services.sh`
> - **Linux users**: See `DOCKER_COMPOSE_LINUX_COMPATIBILITY.md` if `host.docker.internal` doesn't resolve
> - **Override defaults**: Create a `.env` file with `DATABASE__HOST`, `REDIS__HOST`, `STORAGE__ENDPOINT`, etc.

---

---

## 🖥️ Local Development

Running backend directly on your host (not in Docker):

```bash
# Quick start
./scripts/dev-backend.sh

# Or manually
cp .env.local.example .env.local  # first run only
source .env.local
cd frontend && pnpm dev:backend   # delegates to scripts/quick-backend-start.sh
```

📖 See **LOCAL_DEVELOPMENT.md** for complete guide on:
- Avoiding "degraded mode" warnings
- Required services (PostgreSQL, Redis, MinIO)
- Environment configuration
- Troubleshooting

---

## 📚 Documentation Map

### Start Here
1. `docs/INDEX.md` - documentation index
2. `docs/BACKEND_PRODUCTION_GUIDE.md` - production deployment paths
3. `LOCAL_DEVELOPMENT.md` - running backend on host (dev mode)

### Key Guides
- **Infrastructure**: `docs/architecture/INFRASTRUCTURE.md`
- **Compose orchestration**: `scripts/infra.sh`
- **Testing helpers**: `scripts/README.md` and `tests/TESTING_GUIDE.md`

---

## ✅ Status Summary

| Component | Build Status | Warnings | Production Ready |
|-----------|--------------|----------|------------------|
| Platform Admin | ✅ Success | 0 | ✅ Yes |
| Docker Compose | ✅ Ready | N/A | ✅ Yes |
| Multi-Arch Images | ✅ Ready | N/A | ✅ Yes |
| CI/CD | ✅ Configured | N/A | ✅ Yes |

---

For detailed information, see **FINAL_IMPLEMENTATION_SUMMARY.md** 🚀
