# DotMac Platform Services - Makefile

.PHONY: help install test test-fast test-unit test-integration test-cov test-mutation lint format clean doctor doctor-imports verify docker-up docker-down docker-test openapi-client

# Default target
help:
	@echo "DotMac Platform Services - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install all dependencies"
	@echo "  make doctor          Verify Python version and key dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test            Run all tests with coverage"
	@echo "  make test-fast       Run fast unit tests only (no coverage)"
	@echo "  make test-unit       Run unit tests with coverage"
	@echo "  make test-integration Run integration tests with Docker"
	@echo "  make test-cov        Generate HTML coverage report"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up       Start Docker services"
	@echo "  make docker-down     Stop Docker services"
	@echo "  make docker-test     Run integration tests with Docker"
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

# Unit tests with coverage
test-unit:
	poetry run pytest tests/ -m "not integration" \
		--cov=src/dotmac \
		--cov-branch \
		--cov-report=term-missing \
		--cov-fail-under=90

# Full test suite with coverage
test:
	poetry run pytest \
		--cov=src/dotmac \
		--cov-branch \
		--cov-report=term-missing \
		--cov-report=xml \
		--cov-report=html \
		--cov-fail-under=90 \
		-v

# Generate and open coverage report
test-cov:
	poetry run pytest \
		--cov=src/dotmac \
		--cov-branch \
		--cov-report=html \
		--cov-fail-under=90
	@echo "Opening coverage report..."
	@python -m webbrowser htmlcov/index.html || open htmlcov/index.html

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
