#!/bin/bash
# DotMac Platform Services - Complete Startup Script

echo "🚀 Starting DotMac Platform Services"
echo "=====================================\n"

# 1. Start Docker services
echo "📦 Starting Docker services..."
docker-compose up -d
echo "✅ Docker services started\n"

# 2. Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# 3. Get OpenBao root token
echo "🔐 Getting OpenBao root token..."
VAULT_TOKEN=$(docker logs dotmac-openbao 2>&1 | grep "Root Token:" | awk '{print $3}')
echo "   Root Token: $VAULT_TOKEN\n"

# 4. Start FastAPI application with Vault enabled
echo "🌐 Starting FastAPI application..."
echo "   - Authentication: ✅ Enabled"
echo "   - File Storage: ✅ Enabled (MinIO)"
echo "   - Secrets Management: ✅ Enabled (OpenBao)"
echo "   - Analytics: ✅ Enabled"
echo "   - Communications: ✅ Enabled"
echo "   - Search: ✅ Enabled"
echo "   - Data Transfer: ✅ Enabled\n"

# Export environment variables and start server
export VAULT__ENABLED=true
export VAULT__URL=http://localhost:8200
export VAULT__TOKEN=$VAULT_TOKEN

echo "🎯 Starting server on http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "💾 OpenBao UI: http://localhost:8200"
echo "🌸 Flower (Celery): http://localhost:5555"
echo "📊 Jaeger Tracing: http://localhost:16686"
echo "📦 MinIO Console: http://localhost:9001\n"

.venv/bin/uvicorn src.dotmac.platform.main:app --reload --port 8000 --host 0.0.0.0