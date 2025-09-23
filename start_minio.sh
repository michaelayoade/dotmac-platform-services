#!/bin/bash

echo "=========================================="
echo "Starting MinIO Server for DotMac Platform"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Stop any existing MinIO containers
echo "Cleaning up existing containers..."
docker-compose -f docker-compose.minio.yml down 2>/dev/null || true
docker rm -f dotmac-minio dotmac-minio-mc 2>/dev/null || true
echo "✓ Cleanup complete"
echo ""

# Start MinIO using docker-compose
echo "Starting MinIO server..."
docker-compose -f docker-compose.minio.yml up -d

# Wait for MinIO to be healthy
echo ""
echo "Waiting for MinIO to be ready..."
for i in {1..30}; do
    if docker exec dotmac-minio mc ready local 2>/dev/null; then
        echo "✓ MinIO is ready!"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# Export environment variables
echo "Setting environment variables..."
export STORAGE__PROVIDER=minio
export STORAGE__ENDPOINT=localhost:9000
export STORAGE__ACCESS_KEY=minioadmin
export STORAGE__SECRET_KEY=minioadmin123
export STORAGE__BUCKET=dotmac
export STORAGE__USE_SSL=false
export FEATURES__STORAGE_MINIO_ENABLED=true

echo "✓ Environment configured"
echo ""

# Show connection details
echo "=========================================="
echo "MinIO Server Details:"
echo "=========================================="
echo "API Endpoint:    http://localhost:9000"
echo "Console:         http://localhost:9001"
echo "Access Key:      minioadmin"
echo "Secret Key:      minioadmin123"
echo "Default Bucket:  dotmac"
echo ""
echo "To access MinIO Console, open:"
echo "http://localhost:9001"
echo ""
echo "Login with:"
echo "Username: minioadmin"
echo "Password: minioadmin123"
echo "=========================================="