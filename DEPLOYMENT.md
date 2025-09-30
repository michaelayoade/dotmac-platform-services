# Deployment Guide

This guide covers deploying the DotMac Platform Services to production using Docker and Git-based workflows.

## Prerequisites

- Docker & Docker Compose installed on target servers
- Git installed on target servers
- SSH access to deployment servers
- Domain names configured with SSL certificates

## Deployment Architecture

The platform uses a containerized microservices architecture:

- **API Server**: Python FastAPI application
- **Frontend**: Next.js React application
- **Database**: PostgreSQL with automated migrations
- **Cache & Sessions**: Redis
- **Secrets Management**: OpenBao (Vault alternative)
- **Background Tasks**: Celery with Redis broker
- **File Storage**: MinIO (S3-compatible)
- **Monitoring**: Jaeger, Prometheus, Grafana
- **Reverse Proxy**: Nginx with SSL termination

## Server Setup

### 1. Initial Server Configuration

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create deployment directory
sudo mkdir -p /opt/dotmac-platform
sudo chown $USER:$USER /opt/dotmac-platform
```

### 2. Clone Repository

```bash
cd /opt/dotmac-platform
git clone https://github.com/your-org/dotmac-platform-services .
```

### 3. Environment Configuration

```bash
# Copy and configure environment files
cp .env.production.example .env.production

# Edit with your production values
nano .env.production
```

**Required Environment Variables:**

- `SECRET_KEY` - Application secret key
- `JWT_SECRET` - JWT signing secret
- `POSTGRES_PASSWORD` - Database password
- `VAULT_ROOT_TOKEN` - Vault authentication token
- `MINIO_ACCESS_KEY` - Storage access key
- `MINIO_SECRET_KEY` - Storage secret key
- `NEXT_PUBLIC_API_BASE_URL` - Frontend API URL
- `NEXTAUTH_SECRET` - NextAuth secret

### 4. SSL Certificates

```bash
# Create SSL directory
sudo mkdir -p /opt/dotmac-platform/nginx/ssl

# Copy your SSL certificates
sudo cp your-cert.pem /opt/dotmac-platform/nginx/ssl/cert.pem
sudo cp your-key.pem /opt/dotmac-platform/nginx/ssl/key.pem
sudo chmod 600 /opt/dotmac-platform/nginx/ssl/*
```

## Git-Based Deployment Workflow

### Automated Deployment via GitHub Actions

The platform includes automated deployment workflows triggered by:

1. **Staging**: Push to `main` branch
2. **Production**: Tag releases (`v*`) or manual workflow dispatch

#### Required GitHub Secrets:

```yaml
# SSH Access
STAGING_SSH_KEY: "-----BEGIN OPENSSH PRIVATE KEY-----"
STAGING_SERVER: "staging.yourdomain.com"
STAGING_USER: "deploy"

PRODUCTION_SSH_KEY: "-----BEGIN OPENSSH PRIVATE KEY-----"
PRODUCTION_SERVER: "prod.yourdomain.com"
PRODUCTION_USER: "deploy"

# Notifications
SLACK_WEBHOOK: "https://hooks.slack.com/..."
```

#### Deployment Process:

1. **Security Scan**: Trivy vulnerability scanning
2. **Build & Test**: Multi-platform Docker images
3. **Deploy**: Rolling deployment with health checks
4. **Verify**: Automated smoke tests
5. **Notify**: Slack notifications

### Manual Deployment

#### Production Deployment

```bash
# Navigate to deployment directory
cd /opt/dotmac-platform

# Pull latest changes
git fetch origin
git checkout main
git pull origin main

# Update environment
cp .env.production.example .env.production
# Edit .env.production with your values

# Deploy services
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d

# Run migrations
docker-compose -f docker-compose.production.yml exec app migrate

# Verify deployment
docker-compose -f docker-compose.production.yml ps
curl -f http://localhost:8000/health
```

#### Staging Deployment

```bash
# Same process but with staging environment
cp .env.staging.example .env.staging
docker-compose -f docker-compose.production.yml -f docker-compose.staging.override.yml up -d
```

## Service Management

### Starting Services

```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# Start specific service
docker-compose -f docker-compose.production.yml up -d app

# Scale workers
docker-compose -f docker-compose.production.yml up -d --scale celery-worker=4
```

### Stopping Services

```bash
# Stop all services
docker-compose -f docker-compose.production.yml down

# Stop with data cleanup
docker-compose -f docker-compose.production.yml down -v
```

### Viewing Logs

```bash
# All services
docker-compose -f docker-compose.production.yml logs -f

# Specific service
docker-compose -f docker-compose.production.yml logs -f app

# Last 100 lines
docker-compose -f docker-compose.production.yml logs --tail=100 app
```

## Database Management

### Migrations

```bash
# Run migrations
docker-compose -f docker-compose.production.yml exec app migrate

# Check migration status
docker-compose -f docker-compose.production.yml exec app alembic current

# Create new migration
docker-compose -f docker-compose.production.yml exec app alembic revision --autogenerate -m "Description"
```

### Backups

```bash
# Create database backup
docker-compose -f docker-compose.production.yml exec postgres \
  pg_dump -U dotmac_user dotmac_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
docker-compose -f docker-compose.production.yml exec -T postgres \
  psql -U dotmac_user dotmac_prod < backup_20240101_120000.sql
```

## Health Checks & Monitoring

### Application Health

```bash
# API health check
curl http://localhost:8000/health

# Frontend health check
curl http://localhost:3000/api/health

# Container health status
docker-compose -f docker-compose.production.yml ps
```

### Monitoring Dashboards

- **Application Metrics**: http://localhost:3001 (Grafana)
- **Distributed Tracing**: http://localhost:16686 (Jaeger)
- **Prometheus Metrics**: http://localhost:9090
- **MinIO Console**: http://localhost:9001

### Log Aggregation

```bash
# View aggregated logs
docker-compose -f docker-compose.production.yml logs -f --tail=100

# Filter by service
docker-compose -f docker-compose.production.yml logs -f app | grep "ERROR"

# Export logs for analysis
docker-compose -f docker-compose.production.yml logs --no-color > app_logs.txt
```

## Security Considerations

### SSL/TLS

- Use valid SSL certificates from a trusted CA
- Configure HTTP -> HTTPS redirects
- Enable HSTS headers
- Use strong cipher suites

### Network Security

- Use Docker networks for service isolation
- Restrict external port exposure
- Configure firewall rules
- Enable fail2ban for SSH protection

### Secrets Management

- Never commit secrets to Git
- Use environment variables for configuration
- Rotate secrets regularly
- Use Vault for sensitive data

### Access Control

- Use SSH key authentication
- Implement IP whitelisting
- Regular security updates
- Monitor access logs

## Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check service logs
docker-compose -f docker-compose.production.yml logs service-name

# Check container status
docker ps -a

# Restart service
docker-compose -f docker-compose.production.yml restart service-name
```

#### Database Connection Issues

```bash
# Check database logs
docker-compose -f docker-compose.production.yml logs postgres

# Verify database connectivity
docker-compose -f docker-compose.production.yml exec app python -c "
from dotmac.platform.database.session import get_engine
import asyncio
asyncio.run(get_engine().execute('SELECT 1'))
"
```

#### Performance Issues

```bash
# Check resource usage
docker stats

# Monitor application metrics
curl http://localhost:8000/metrics

# Check database performance
docker-compose -f docker-compose.production.yml exec postgres \
  psql -U dotmac_user -d dotmac_prod -c "
    SELECT query, calls, total_time, mean_time
    FROM pg_stat_statements
    ORDER BY total_time DESC LIMIT 10;"
```

### Recovery Procedures

#### Application Rollback

```bash
# Rollback to previous git commit
git reset --hard HEAD~1

# Rebuild and redeploy
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d
```

#### Database Restore

```bash
# Stop application
docker-compose -f docker-compose.production.yml stop app

# Restore database from backup
docker-compose -f docker-compose.production.yml exec -T postgres \
  psql -U dotmac_user dotmac_prod < backup.sql

# Restart application
docker-compose -f docker-compose.production.yml start app
```

## CI/CD Pipeline Status

### Current Test Coverage

- **Backend**: 38% (baseline, improving to 90%)
- **Frontend**: 70% (plugin components)

### Pipeline Gates

- **Security**: Trivy vulnerability scanning ✅
- **Quality**: Linting, type checking ✅
- **Testing**: Unit tests, integration tests ⚠️ (needs improvement)
- **Build**: Multi-platform Docker images ✅
- **Deploy**: Zero-downtime rolling deployments ✅

### Recommendations for CI/CD Improvement

1. **Fix Frontend Tests**: Address 17 failing test suites
2. **Increase Backend Coverage**: Target 90% test coverage
3. **Add E2E Tests**: Playwright integration tests
4. **Performance Testing**: Load testing with k6
5. **Security Scanning**: SAST/DAST integration

### Current Issues

❌ **Frontend Tests Failing**: 17/17 test suites failing
❌ **Backend Coverage Low**: Currently 38%, needs 90%
⚠️  **E2E Tests**: Not fully implemented
✅ **Docker Builds**: Working correctly
✅ **Deployment Pipeline**: Ready for production

The platform is **deployment-ready** with robust containerization and Git-based workflows, but **test reliability needs improvement** before production use.