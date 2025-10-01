#!/bin/bash
# Test script to verify end-to-end observability

set -e

echo "🔍 Testing DotMac Platform Observability..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check OTEL Collector
echo "📊 Checking OpenTelemetry Collector..."
if curl -s http://localhost:13133 > /dev/null 2>&1; then
    echo "✅ OTEL Collector is running on :13133"
else
    echo "⚠️  OTEL Collector not running. Starting observability stack..."
    docker-compose -f docker-compose.observability.yml up -d
    sleep 5
fi

# Check Jaeger
echo "📈 Checking Jaeger..."
if curl -s http://localhost:16686 > /dev/null 2>&1; then
    echo "✅ Jaeger UI available at http://localhost:16686"
else
    echo "❌ Jaeger is not running"
fi

# Check Prometheus
echo "📊 Checking Prometheus..."
if curl -s http://localhost:9090 > /dev/null 2>&1; then
    echo "✅ Prometheus available at http://localhost:9090"
else
    echo "❌ Prometheus is not running"
fi

# Check Grafana
echo "📊 Checking Grafana..."
if curl -s http://localhost:3400 > /dev/null 2>&1; then
    echo "✅ Grafana available at http://localhost:3400"
else
    echo "❌ Grafana is not running"
fi

echo ""
echo "🎉 Observability Stack Status:"
echo "   - OTEL Collector: http://localhost:4318 (HTTP), :4317 (gRPC)"
echo "   - Jaeger UI:      http://localhost:16686"
echo "   - Prometheus:     http://localhost:9090"
echo "   - Grafana:        http://localhost:3400 (admin/admin)"
echo ""
echo "📝 Next steps:"
echo "   1. Start backend:  poetry run uvicorn dotmac.platform.main:app --reload"
echo "   2. Start frontend: cd frontend/apps/base-app && pnpm dev"
echo "   3. Visit app:      http://localhost:3000"
echo "   4. View traces:    http://localhost:16686"
echo ""
echo "🔗 To test end-to-end tracing:"
echo "   1. Login to the app"
echo "   2. Navigate to Customers page"
echo "   3. Create a new customer"
echo "   4. Open Jaeger and search for 'dotmac-frontend' or 'dotmac-platform'"
echo "   5. You should see traces spanning frontend → backend → database!"
