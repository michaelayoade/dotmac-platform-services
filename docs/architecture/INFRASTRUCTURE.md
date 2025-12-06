# Infrastructure Reference

This document describes the shared services brought up by `docker-compose.infra.yml`. The compose file creates the `dotmac-network` bridge that the application compose files re-use.

## Stack
- PostgreSQL (`dotmac-postgres`, 5432) with persistent volume `postgres_data`
- Redis (`dotmac-redis`, 6379) with password protection and volume `redis_data`
- MinIO (`dotmac-minio`, 9000/9001) with volume `minio_data`
- NetBox (`dotmac-netbox`) plus Postgres/Redis sidecars for IPAM/DCIM
- MeiliSearch (`dotmac-meilisearch`, 7700) with volume `meilisearch_data`
- Observability: Prometheus (9090), Grafana (3000), Loki (3100), Jaeger (16686/4317/4318)
- Secrets: OpenBao/Vault dev mode (8200) using token from `VAULT__TOKEN`
- Alertmanager (9093) using config in `monitoring/alertmanager/alertmanager.yml`

## Usage
```bash
# Start core infrastructure and create the shared docker network
docker compose -f docker-compose.infra.yml up -d

# Check status
docker compose -f docker-compose.infra.yml ps

# Tear down (keeps volumes)
docker compose -f docker-compose.infra.yml down
```

The helper `scripts/infra.sh` will call the same compose file when you run `./scripts/infra.sh infra start` or `./scripts/infra.sh all start`.
