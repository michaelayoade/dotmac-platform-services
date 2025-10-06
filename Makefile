# DotMac Platform Services - Makefile

.PHONY: help install test test-fast test-unit test-integration test-cov test-mutation test-slow test-comprehensive lint format clean doctor doctor-imports verify docker-up docker-down docker-test openapi-client infra-up infra-down infra-status run run-dev seed-db dev dev-backend dev-frontend dev-all

# Default target
help:
	@echo "DotMac Platform Services - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install all dependencies"
	@echo "  make doctor          Verify Python version and key dependencies"
	@echo "  make seed-db         Seed database with test data"
	@echo ""
	@echo "Testing:"
	@echo "  make test            Run all tests with coverage"
	@echo "  make test-fast       Run fast unit tests only (no coverage)"
	@echo "  make test-unit       Run unit tests with coverage"
	@echo "  make test-slow       Run only slow/comprehensive tests"
	@echo "  make test-integration Run integration tests with Docker"
	@echo "  make test-cov        Generate HTML coverage report"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make infra-up        Start all infrastructure services"
	@echo "  make infra-down      Stop all infrastructure services"
	@echo "  make infra-status    Check infrastructure health"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up       Start Docker services"
	@echo "  make docker-down     Stop Docker services"
	@echo "  make docker-test     Run integration tests with Docker"
	@echo ""
	@echo "Running:"
	@echo "  make run             Start the application"
	@echo "  make run-dev         Start in development mode with hot reload"
	@echo "  make dev-all         Start backend + frontend (requires infra running)"
	@echo "  make dev-backend     Start backend only (port 8000)"
	@echo "  make dev-frontend    Start frontend only (port 3000)"
	@echo "  make dev             Start infra + backend + frontend (full stack)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint            Run all linters"
	@echo "  make format          Auto-format code"
	@echo "  make clean           Remove build artifacts"
	@echo "  make openapi-client  Export OpenAPI spec and regenerate TypeScript client"

# Installation
install:
	poetry install --with dev

# Fast unit tests without coverage (for development)
test-fast:
	poetry run pytest tests/ -m "not integration and not slow" -x --tb=short -q

# Unit tests with coverage (aligned with CI)
test-unit:
	poetry run pytest tests/ -m "not integration" \
		--cov=src/dotmac \
		--cov-branch \
		--cov-report=term-missing \
		--cov-fail-under=85

# Full test suite with coverage (aligned with CI)
test:
	poetry run pytest \
		--cov=src/dotmac \
		--cov-branch \
		--cov-report=term-missing \
		--cov-report=xml \
		--cov-report=html \
		--cov-fail-under=85 \
		-v

# Generate and open coverage report (aligned with CI)
test-cov:
	poetry run pytest \
		--cov=src/dotmac \
		--cov-branch \
		--cov-report=html \
		--cov-fail-under=85
	@echo "Opening coverage report..."
	@python -m webbrowser htmlcov/index.html || open htmlcov/index.html

# Run only slow and comprehensive tests
test-slow:
	poetry run pytest tests/ -m "slow or comprehensive" -v --tb=short

# Run comprehensive tests specifically
test-comprehensive:
	poetry run pytest tests/ -m "comprehensive" -v --tb=short

# Environment diagnostics
doctor:
	@echo "Checking Python version (>= 3.12 required)..."
	@poetry run python -c "import sys; m,n=sys.version_info[:2]; print(f'Python {m}.{n}'); assert (m,n)>=(3,12), 'Python 3.12+ required for modern typing and Pydantic v2'; print('\u2713 Python version OK')"
	@echo "Checking core runtime dependencies..."
	@poetry run python scripts/check_deps.py runtime
	@echo "Checking test/dev dependencies..."
	@poetry run python scripts/check_deps.py dev || true
	@echo "✓ Environment looks good!"

doctor-imports:
	@echo "Verifying high-level module imports..."
	@PYTHONPATH=src poetry run python scripts/verify_imports.py || true

verify: doctor doctor-imports

# Generate OpenAPI specification and TypeScript client types
openapi-client:
	poetry run python scripts/export_openapi.py --mode=$(MODE)
	cd frontend && pnpm generate:api-client

# Linting
lint:
	poetry run black --check .
	poetry run isort --check-only .
	poetry run ruff check .
	poetry run bandit -r src/ -ll

# Auto-format code
format:
	poetry run black .
	poetry run isort .
	poetry run ruff check --fix .

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info htmlcov/ .coverage coverage.xml
	rm -rf .pytest_cache/ .ruff_cache/ .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Docker commands
docker-up:
	docker compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Docker services are running"

docker-down:
	docker compose down -v

docker-test: docker-up
	@echo "Running integration tests..."
	poetry run pytest tests/integration/test_docker_services.py -v --tb=short || true
	@echo ""
	@read -p "Stop Docker services? (y/N): " stop; \
	if [ "$$stop" = "y" ] || [ "$$stop" = "Y" ]; then \
		make docker-down; \
	fi

# Integration tests
test-integration:
	@./scripts/run_integration_tests.sh

# Infrastructure Management
infra-up:
	@./scripts/check_infra.sh up

infra-down:
	@./scripts/check_infra.sh down

infra-status:
	@./scripts/check_infra.sh status

# Run application
run:
	@poetry run python -m src.dotmac.platform.main

run-dev:
	@ENVIRONMENT=development poetry run python -m src.dotmac.platform.main

# Database seeding
seed-db:
	@echo "🌱 Seeding database with test data..."
	@poetry run python scripts/seed_data.py --env=development
	@echo "✅ Database seeded successfully!"

seed-db-clean:
	@echo "🧹 Clearing and re-seeding database..."
	@poetry run python scripts/seed_data.py --env=development --clear
	@echo "✅ Database re-seeded successfully!"

# Development mode - Backend only
dev-backend:
	@echo "🚀 Starting backend on http://localhost:8000"
	@echo "   API docs: http://localhost:8000/docs"
	@ENVIRONMENT=development poetry run uvicorn src.dotmac.platform.main:app --reload --host 0.0.0.0 --port 8000

# Development mode - Frontend only
dev-frontend:
	@echo "🚀 Starting frontend on http://localhost:3000"
	@cd frontend/apps/base-app && PORT=3000 pnpm dev

# Development mode - Backend + Frontend (requires infra)
dev-all:
	@echo "🚀 Starting backend + frontend..."
	@echo ""
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:3000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo ""
	@$(MAKE) -j2 dev-backend dev-frontend

# Full development stack (infra + backend + frontend)
dev:
	@echo "🚀 Starting full development stack..."
	@echo ""
	@./scripts/check_infra.sh dev
	@echo ""
	@echo "✨ Full stack ready!"
	@echo ""
	@echo "  📦 Infrastructure:"
	@echo "    PostgreSQL:  localhost:5432"
	@echo "    Redis:       localhost:6379"
	@echo "    Vault:       localhost:8200"
	@echo "    MinIO API:   localhost:9000"
	@echo "    MinIO UI:    localhost:9001"
	@echo "    Jaeger UI:   http://localhost:16686"
	@echo "    Flower UI:   http://localhost:5555"
	@echo ""
	@echo "  🚀 Application:"
	@echo "    Backend:     http://localhost:8000"
	@echo "    Frontend:    http://localhost:3000"
	@echo "    API Docs:    http://localhost:8000/docs"
	@echo ""
	@echo "Press Ctrl+C to stop all services"
	@echo ""
	@$(MAKE) dev-all
