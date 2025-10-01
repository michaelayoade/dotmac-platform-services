#!/bin/bash

# DotMac Platform Services - Integration Test Runner
# Starts Docker services and runs integration tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
COMPOSE_TEST_FILE="docker-compose.test.yml"
WAIT_TIMEOUT=60

echo -e "${BLUE}DotMac Platform Services - Integration Test Runner${NC}"
echo "=================================================="

# Function to check if a service is ready
check_service() {
    local service=$1
    local check_cmd=$2
    local max_attempts=30
    local attempt=0

    echo -n "Waiting for $service..."

    while [ $attempt -lt $max_attempts ]; do
        if eval "$check_cmd" >/dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done

    echo -e " ${RED}✗${NC}"
    return 1
}

# Function to cleanup
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    docker compose -f $COMPOSE_FILE down -v
    exit ${1:-0}
}

# Trap cleanup on exit
trap cleanup SIGINT SIGTERM

# Step 1: Check Docker and Docker Compose
echo -e "\n${BLUE}Step 1: Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker and Docker Compose are installed"

# Step 2: Stop any existing containers
echo -e "\n${BLUE}Step 2: Stopping existing containers...${NC}"
docker compose -f $COMPOSE_FILE down -v || true

# Step 3: Start Docker services
echo -e "\n${BLUE}Step 3: Starting Docker services...${NC}"
docker compose -f $COMPOSE_FILE up -d

# Step 4: Wait for services to be ready
echo -e "\n${BLUE}Step 4: Waiting for services to be ready...${NC}"

# Check PostgreSQL
check_service "PostgreSQL" "docker exec dotmac-postgres pg_isready -U dotmac" || {
    echo -e "${RED}PostgreSQL failed to start${NC}"
    cleanup 1
}

# Check Redis
check_service "Redis" "docker exec dotmac-redis redis-cli ping" || {
    echo -e "${RED}Redis failed to start${NC}"
    cleanup 1
}

# Check RabbitMQ
check_service "RabbitMQ" "docker exec dotmac-rabbitmq rabbitmqctl status" || {
    echo -e "${RED}RabbitMQ failed to start${NC}"
    cleanup 1
}

# Check Vault/OpenBao
check_service "Vault/OpenBao" "curl -s http://localhost:8200/v1/sys/health" || {
    echo -e "${RED}Vault/OpenBao failed to start${NC}"
    cleanup 1
}

# Check MinIO
check_service "MinIO" "curl -s http://localhost:9000/minio/health/live" || {
    echo -e "${RED}MinIO failed to start${NC}"
    cleanup 1
}

# Check Meilisearch
check_service "Meilisearch" "curl -s http://localhost:7700/health" || {
    echo -e "${RED}Meilisearch failed to start${NC}"
    cleanup 1
}

echo -e "\n${GREEN}All services are ready!${NC}"

# Step 5: Initialize services
echo -e "\n${BLUE}Step 5: Initializing services...${NC}"

# Initialize Vault
echo "Initializing Vault secrets engine..."
docker exec dotmac-openbao bao secrets enable -path=secret kv-v2 2>/dev/null || true

# Initialize MinIO buckets
echo "Creating MinIO buckets..."
docker exec dotmac-minio mc config host add minio http://localhost:9000 minioadmin minioadmin 2>/dev/null || true
docker exec dotmac-minio mc mb minio/dotmac 2>/dev/null || true

echo -e "${GREEN}✓${NC} Services initialized"

# Step 6: Start Celery worker
echo -e "\n${BLUE}Step 6: Starting Celery worker...${NC}"

# Check if virtual environment exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif command -v poetry &> /dev/null; then
    eval "$(poetry env info --path)/bin/activate"
fi

# Start Celery worker in background
celery -A dotmac.platform.tasks.celery_app worker --loglevel=info &
CELERY_PID=$!
sleep 5

echo -e "${GREEN}✓${NC} Celery worker started (PID: $CELERY_PID)"

# Step 7: Run integration tests
echo -e "\n${BLUE}Step 7: Running integration tests...${NC}"

# Export environment variables
export DATABASE_URL="postgresql+asyncpg://dotmac:dotmac_password@localhost:5432/dotmac"
export REDIS_URL="redis://localhost:6379/0"
export VAULT_URL="http://localhost:8200"
export VAULT_TOKEN="root-token"
export CELERY_BROKER_URL="amqp://admin:admin@localhost:5672//"
export MINIO_ENDPOINT="localhost:9000"
export MINIO_ACCESS_KEY="minioadmin"
export MINIO_SECRET_KEY="minioadmin"
export MEILISEARCH_URL="http://localhost:7700"
export MEILISEARCH_KEY="masterKey"

# Run tests
echo ""
pytest tests/integration/test_docker_services.py -v --tb=short

TEST_EXIT_CODE=$?

# Step 8: Show service logs if tests failed
if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo -e "\n${YELLOW}Tests failed. Showing recent logs...${NC}"
    echo -e "\n${BLUE}PostgreSQL logs:${NC}"
    docker logs dotmac-postgres --tail 20
    echo -e "\n${BLUE}Redis logs:${NC}"
    docker logs dotmac-redis --tail 20
fi

# Step 9: Stop Celery worker
echo -e "\n${BLUE}Stopping Celery worker...${NC}"
kill $CELERY_PID 2>/dev/null || true

# Step 10: Cleanup (optional)
read -p "Do you want to stop Docker services? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cleanup $TEST_EXIT_CODE
else
    echo -e "${GREEN}Docker services are still running${NC}"
    echo -e "${YELLOW}To stop them later, run: docker compose down -v${NC}"
    exit $TEST_EXIT_CODE
fi