#!/usr/bin/env bash
# Infrastructure health check and startup script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

MODE="${1:-check}"

# Function to check if a container is running
check_container() {
    local container_name=$1
    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        return 0
    else
        return 1
    fi
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service health
wait_for_service() {
    local service=$1
    local max_attempts=30
    local attempt=1

    echo -n "  Waiting for $service to be healthy"

    while [ $attempt -le $max_attempts ]; do
        if docker inspect --format='{{.State.Health.Status}}' $service 2>/dev/null | grep -q "healthy"; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done

    echo -e " ${YELLOW}⚠${NC} (continuing anyway)"
    return 1
}

# Check and start infrastructure
if [ "$MODE" = "up" ] || [ "$MODE" = "dev" ]; then
    echo -e "${BLUE}Checking infrastructure services...${NC}"
    echo ""

    # Define all services to check (container:port)
    SERVICES="dotmac-postgres:5432 dotmac-redis:6379 dotmac-openbao:8200 dotmac-minio:9000 dotmac-jaeger:16686"

    NEED_START=""
    ALREADY_RUNNING=""

    # Check each service
    for service_info in $SERVICES; do
        container="${service_info%%:*}"
        port="${service_info##*:}"

        if check_container "$container"; then
            ALREADY_RUNNING="$ALREADY_RUNNING $container"
            echo -e "  ${GREEN}✓${NC} $container (running)"
        elif check_port "$port"; then
            echo -e "  ${YELLOW}⚠${NC} Port $port in use (container not running, possible conflict)"
        else
            NEED_START="$NEED_START $container"
            echo -e "  ${RED}✗${NC} $container (not running)"
        fi
    done

    echo ""

    # Start services if needed
    if [ -n "$NEED_START" ]; then
        echo -e "${BLUE}Starting services:${NEED_START}${NC}"
        echo ""

        # Start all core services with all profiles
        docker-compose up -d postgres redis openbao minio \
            --profile storage \
            --profile observability \
            --profile celery 2>&1 | grep -v "is up-to-date" || true

        echo ""
        echo -e "${BLUE}Waiting for services to be ready...${NC}"

        # Wait for critical services
        wait_for_service "dotmac-postgres"
        wait_for_service "dotmac-redis"
        wait_for_service "dotmac-openbao"
        wait_for_service "dotmac-minio"

        echo ""
        echo -e "${GREEN}✅ All services started successfully!${NC}"
    elif [ -n "$ALREADY_RUNNING" ]; then
        echo -e "${GREEN}✅ All services already running!${NC}"
    fi

    echo ""

    # Show running services
    echo -e "${BLUE}Running infrastructure:${NC}"
    docker ps --filter "name=dotmac-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -20

elif [ "$MODE" = "status" ]; then
    # Just show status
    echo -e "${BLUE}Infrastructure Status:${NC}"
    echo ""
    docker ps --filter "name=dotmac-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

elif [ "$MODE" = "down" ]; then
    echo -e "${YELLOW}Stopping all infrastructure...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Infrastructure stopped${NC}"

else
    echo "Usage: $0 {up|dev|status|down}"
    exit 1
fi
