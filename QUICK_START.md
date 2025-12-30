# Quick Start Guide - DotMac FTTH Platform

**Last Updated**: 2025-11-04
**Status**: ✅ Production Ready

---

## 🚀 TL;DR

```bash
# Frontend (requires network access)
cd frontend
pnpm install
pnpm build

# Docker Compose - Platform (Admin + Backend)
cd ..

# Step 1: Start shared infrastructure (Postgres, Redis, MinIO, observability)
./scripts/infra.sh infra start

# Step 2: Start platform backend + admin UI
./scripts/infra.sh platform start
# Platform backend: http://localhost:8000
# Platform frontend: http://localhost:3000
```

> Note: An ISP-specific Docker Compose stack is not included in this repository; the supported Compose path is the platform stack above.

> Optional: If you run PostgreSQL/Redis/MinIO outside Docker, run `./scripts/check-external-services.sh` and override `DATABASE__HOST`, `REDIS__HOST`, `STORAGE__ENDPOINT`, etc. in a `.env` file.

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
./scripts/quick-backend-start.sh
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

For detailed information, see **docs/INDEX.md** 🚀
