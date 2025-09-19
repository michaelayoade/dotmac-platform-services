#!/bin/bash
set -e

# Production entrypoint script for DotMac Platform API
# Handles pre-start checks, migrations, and service startup

echo "Starting DotMac Platform API..."

# Function to wait for service
wait_for_service() {
    local host="$1"
    local port="$2"
    local service_name="$3"
    local max_attempts="${4:-30}"
    local attempt=1

    echo "Waiting for $service_name at $host:$port..."

    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "✓ $service_name is ready"
            return 0
        fi
        echo "  Attempt $attempt/$max_attempts: $service_name not ready, waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo "✗ Failed to connect to $service_name after $max_attempts attempts"
    return 1
}

# Function to run database migrations
run_migrations() {
    if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
        echo "Running database migrations..."
        alembic upgrade head
        echo "✓ Migrations completed"
    else
        echo "Skipping migrations (RUN_MIGRATIONS != true)"
    fi
}

# Function to run health checks
run_health_checks() {
    echo "Running pre-start health checks..."

    # Check database connectivity
    if [ -n "$DATABASE_URL" ]; then
        # Extract host and port from DATABASE_URL
        DB_HOST=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
        DB_PORT=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        wait_for_service "${DB_HOST:-postgres}" "${DB_PORT:-5432}" "PostgreSQL"
    fi

    # Check Redis connectivity
    if [ -n "$REDIS_URL" ]; then
        REDIS_HOST=$(echo "$REDIS_URL" | sed -n 's/.*\/\/\([^:]*\):.*/\1/p')
        REDIS_PORT=$(echo "$REDIS_URL" | sed -n 's/.*:\([0-9]*\).*/\1/p' | tail -1)
        wait_for_service "${REDIS_HOST:-redis}" "${REDIS_PORT:-6379}" "Redis"
    fi

    # Check RabbitMQ connectivity (for Celery)
    if [ -n "$CELERY_BROKER_URL" ] || [ -n "$RABBITMQ_URL" ]; then
        BROKER_URL="${CELERY_BROKER_URL:-$RABBITMQ_URL}"
        RABBITMQ_HOST=$(echo "$BROKER_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
        RABBITMQ_PORT=$(echo "$BROKER_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p' | tail -1)
        wait_for_service "${RABBITMQ_HOST:-rabbitmq}" "${RABBITMQ_PORT:-5672}" "RabbitMQ"
    fi

    echo "✓ All health checks passed"
}

# Main execution
case "$1" in
    api)
        run_health_checks
        run_migrations

        echo "Starting Gunicorn API server..."
        exec gunicorn dotmac.platform.main:app \
            --worker-class "${GUNICORN_WORKER_CLASS}" \
            --workers "${GUNICORN_WORKERS}" \
            --bind "${GUNICORN_BIND}" \
            --max-requests "${GUNICORN_MAX_REQUESTS}" \
            --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER}" \
            --timeout "${GUNICORN_TIMEOUT}" \
            --keepalive "${GUNICORN_KEEPALIVE}" \
            --access-logfile "${GUNICORN_ACCESS_LOG}" \
            --error-logfile "${GUNICORN_ERROR_LOG}" \
            --log-level "${GUNICORN_LOG_LEVEL}" \
            --preload
        ;;

    dev)
        run_health_checks
        run_migrations

        echo "Starting development server..."
        exec uvicorn dotmac.platform.main:app \
            --host 0.0.0.0 \
            --port 8000 \
            --reload \
            --log-level debug
        ;;

    migrate)
        run_health_checks
        echo "Running migrations only..."
        alembic upgrade head
        echo "✓ Migrations completed successfully"
        ;;

    shell)
        echo "Starting interactive shell..."
        exec python
        ;;

    *)
        echo "Unknown command: $1"
        echo "Available commands: api, dev, migrate, shell"
        exit 1
        ;;
esac