#!/usr/bin/env bash
#
# DotMac Infrastructure Helper (platform only)
# --------------------------------------------
# Manages the platform stacks:
#   - Infrastructure: docker-compose.infra.yml
#   - Platform API + admin UI: docker-compose.base.yml
#   - Worker: docker-compose.prod.yml
#
# Usage:
#   ./scripts/infra.sh infra start|stop|restart|status|logs|clean
#   ./scripts/infra.sh platform start|stop|restart|status|logs|clean
#   ./scripts/infra.sh all start|stop|restart|status|logs|clean
#

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

COMPOSE_INFRA="docker-compose.infra.yml"
COMPOSE_PLATFORM="docker-compose.base.yml"
COMPOSE_WORKER="docker-compose.prod.yml"

INFRA_SERVICES=(
    "postgres:5432:PostgreSQL Database"
    "redis:6379:Redis Cache"
    "minio:9000:MinIO Object Storage"
    "netbox:8080:NetBox (IPAM/DCIM)"
    "meilisearch:7700:MeiliSearch"
    "prometheus:9090:Prometheus"
    "grafana:3000:Grafana Dashboards"
    "loki:3100:Loki (Logs)"
    "jaeger:16686:Jaeger UI (Tracing)"
)

PLATFORM_SERVICES=(
    "platform-backend:8000:Platform API"
    "platform-frontend:3000:Platform Admin UI"
    "platform-worker::Celery Worker (prod compose)"
)

print_header() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  ${CYAN}DotMac Platform - Compose Service Manager${NC}        ${BLUE}║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_usage() {
    cat <<EOF
${CYAN}Usage:${NC}
  ./scripts/infra.sh <mode> <command> [options]

${CYAN}Modes:${NC}
  ${GREEN}infra${NC}       Infrastructure stack (postgres, redis, minio, observability)
  ${GREEN}platform${NC}    Platform backend + admin frontend
  ${GREEN}all${NC}         infra + platform + worker

${CYAN}Commands:${NC}
  ${GREEN}start${NC}       Start services
  ${GREEN}stop${NC}        Stop services
  ${GREEN}restart${NC}     Restart services
  ${GREEN}status${NC}      Show service status and ports
  ${GREEN}logs${NC}        Tail service logs (optional service name)
  ${GREEN}clean${NC}       Remove containers and volumes (destructive)

${CYAN}Examples:${NC}
  ./scripts/infra.sh infra start
  ./scripts/infra.sh platform status
  ./scripts/infra.sh all start
EOF
}

check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}✗ Docker daemon is not available${NC}"
        echo -e "${YELLOW}→ Start Docker Desktop or Docker Engine and retry${NC}"
        exit 1
    fi
}

container_name() {
    local service=$1
    local compose_file=$2

    if [[ "${compose_file}" == "${COMPOSE_INFRA}" ]]; then
        echo "dotmac-${service}"
    else
        # Application services use project-based names
        echo "${COMPOSE_PROJECT_NAME:-$(basename "$(pwd)")}-${service}-1"
    fi
}

get_container_status() {
    local container=$1
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        echo "running"
    elif docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
        echo "stopped"
    else
        echo "not_created"
    fi
}

is_healthy() {
    local container=$1
    local health
    health=$(docker inspect --format='{{.State.Health.Status}}' "${container}" 2>/dev/null || echo "none")
    if [[ "${health}" == "healthy" ]]; then
        return 0
    fi

    if [[ "${health}" == "none" ]]; then
        local status
        status=$(docker inspect --format='{{.State.Status}}' "${container}" 2>/dev/null || echo "unknown")
        [[ "${status}" == "running" ]]
        return
    fi

    return 1
}

show_services_status() {
    local compose_file=$1
    shift
    local services=("$@")

    for entry in "${services[@]}"; do
        IFS=':' read -r service port description <<<"${entry}"
        local container
        container=$(container_name "${service}" "${compose_file}")
        local status
        status=$(get_container_status "${container}")

        case "${status}" in
            running)
                if is_healthy "${container}"; then
                    echo -e "  ${GREEN}✓${NC} ${service} (${description}) - ${GREEN}healthy${NC}"
                else
                    echo -e "  ${YELLOW}◆${NC} ${service} (${description}) - ${YELLOW}starting${NC}"
                fi
                ;;
            stopped)
                echo -e "  ${RED}✗${NC} ${service} (${description}) - ${RED}stopped${NC}"
                ;;
            *)
                echo -e "  ${YELLOW}○${NC} ${service} (${description}) - ${YELLOW}not created${NC}"
                ;;
        esac

        if [[ -n "${port}" ]]; then
            echo -e "    ${CYAN}→${NC} http://localhost:${port}"
        fi
    done

    echo ""
    docker compose -f "${compose_file}" ps --status running --status exited
}

start_infra() {
    echo -e "${CYAN}Starting infrastructure services...${NC}"
    docker compose -f "${COMPOSE_INFRA}" up -d
    echo -e "${GREEN}✓ Waiting for infrastructure services to become healthy...${NC}"
    sleep 5
    echo ""
    status_infra
}

start_platform() {
    echo -e "${CYAN}Starting platform services...${NC}"
    docker compose -f "${COMPOSE_PLATFORM}" up -d platform-backend platform-frontend
    echo ""
    status_platform
}

start_all() {
    start_infra
    echo ""
    start_platform
    echo ""
    echo -e "${CYAN}Starting worker...${NC}"
    docker compose -f "${COMPOSE_WORKER}" up -d platform-worker
}

stop_infra() {
    echo -e "${CYAN}Stopping infrastructure services...${NC}"
    docker compose -f "${COMPOSE_INFRA}" down
}

stop_platform() {
    echo -e "${CYAN}Stopping platform services...${NC}"
    docker compose -f "${COMPOSE_PLATFORM}" down
    docker compose -f "${COMPOSE_WORKER}" down || true
}

stop_all() {
    stop_platform
    stop_infra
}

restart_platform() {
    echo -e "${CYAN}Restarting platform services...${NC}"
    docker compose -f "${COMPOSE_PLATFORM}" up -d --force-recreate platform-backend platform-frontend
    echo ""
    docker compose -f "${COMPOSE_WORKER}" up -d --force-recreate platform-worker
    echo ""
    status_platform
}

restart_all() {
    stop_all
    echo ""
    start_all
}

status_infra() {
    echo -e "${CYAN}Infrastructure services:${NC}"
    show_services_status "${COMPOSE_INFRA}" "${INFRA_SERVICES[@]}"
}

status_platform() {
    echo -e "${CYAN}Platform services:${NC}"
    show_services_status "${COMPOSE_PLATFORM}" "${PLATFORM_SERVICES[@]}"
}

status_all() {
    status_infra
    echo ""
    status_platform
}

logs_platform() {
    local service=${1:-}
    docker compose -f "${COMPOSE_PLATFORM}" logs -f ${service}
}

logs_all() {
    echo -e "${YELLOW}Monitoring platform stack. Ctrl+C to exit.${NC}"
    docker compose -f "${COMPOSE_PLATFORM}" logs -f
}

clean_infra() {
    echo -e "${RED}⚠ This will remove infrastructure containers and volumes.${NC}"
    read -p "Continue? (yes/no): " answer
    if [[ "${answer}" == "yes" ]]; then
        docker compose -f "${COMPOSE_INFRA}" down -v
    else
        echo "Aborted."
    fi
}

clean_platform() {
    echo -e "${RED}⚠ This will remove platform containers and volumes.${NC}"
    read -p "Continue? (yes/no): " answer
    if [[ "${answer}" == "yes" ]]; then
        docker compose -f "${COMPOSE_PLATFORM}" down -v
        docker compose -f "${COMPOSE_WORKER}" down -v || true
    else
        echo "Aborted."
    fi
}

clean_all() {
    clean_platform
    clean_infra
}

if [[ $# -lt 1 ]] || [[ $1 == "--help" ]] || [[ $1 == "-h" ]]; then
    print_header
    print_usage
    exit 0
fi

MODE=$1
COMMAND=${2:-status}
ARG=${3:-}

check_docker

case "${MODE}" in
    infra)
        case "${COMMAND}" in
            start) start_infra ;;
            stop) stop_infra ;;
            restart) stop_infra; start_infra ;;
            status) status_infra ;;
            logs) docker compose -f "${COMPOSE_INFRA}" logs -f ;;
            clean) clean_infra ;;
            *) echo -e "${RED}Unknown command '${COMMAND}' for infra mode${NC}"; print_usage; exit 1 ;;
        esac
        ;;
    platform)
        case "${COMMAND}" in
            start) start_platform ;;
            stop) stop_platform ;;
            restart) restart_platform ;;
            status) status_platform ;;
            logs) logs_platform "${ARG}" ;;
            clean) clean_platform ;;
            *) echo -e "${RED}Unknown command '${COMMAND}' for platform mode${NC}"; print_usage; exit 1 ;;
        esac
        ;;
    all)
        case "${COMMAND}" in
            start) start_all ;;
            stop) stop_all ;;
            restart) restart_all ;;
            status) status_all ;;
            logs) logs_all ;;
            clean) clean_all ;;
            *) echo -e "${RED}Unknown command '${COMMAND}' for all mode${NC}"; print_usage; exit 1 ;;
        esac
        ;;
    *)
        echo -e "${RED}Unknown mode '${MODE}'${NC}"
        print_usage
        exit 1
        ;;
esac
