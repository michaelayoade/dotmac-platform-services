# Scripts Directory

This directory contains utility scripts for development, testing, and deployment of the DotMac Platform Services.

## Directory Structure

```
scripts/
├── tests/           # API and integration test scripts
├── demos/           # Demonstration scripts for features
├── obsolete/        # Deprecated scripts (to be removed)
└── *.sh/*.py        # Various utility scripts
```

## Main Scripts

### Development & Setup

- **`setup-dev-tools.sh`** - Install development dependencies and tools
- **`setup_vault.sh`** - Configure HashiCorp Vault for development
- **`setup_secrets.sh`** - Initialize secrets in Vault
- **`setup_minio_secrets.py`** - Configure MinIO storage secrets
- **`cleanup.sh`** - Clean and organize project structure

### Database

- **`init-db.sql`** - SQL script for database initialization
- **`seed_data.py`** - Populate database with test data

### Testing

- **`run_integration_tests.sh`** - Execute integration test suite
- **`run_tests.sh`** - Run unit tests
- **`tests/test_api.py`** - Test API endpoints without auth
- **`tests/test_api_detailed.py`** - Detailed API endpoint testing

### Docker & Deployment

- **`docker-entrypoint.sh`** - Docker container entry point
- **`celery-entrypoint.sh`** - Celery worker entry point
- **`deploy.sh`** - Deployment script
- **`celery_worker.py`** - Celery worker configuration

### Observability

- **`otel-collector.yaml`** - OpenTelemetry collector configuration
- **`otel-collector-simple.yaml`** - Simplified OTEL config
- **`prometheus.yml`** - Prometheus monitoring configuration

### Utilities

- **`export_openapi.py`** - Export OpenAPI specification
- **`check_deps.py`** - Check Python dependencies
- **`verify_imports.py`** - Verify Python imports are valid

### Demos

- **`demos/demo_file_storage.py`** - Demonstrate file storage functionality

## Usage Examples

### Set up development environment
```bash
./scripts/setup-dev-tools.sh
```

### Initialize Vault with secrets
```bash
./scripts/setup_vault.sh
./scripts/setup_secrets.sh
```

### Run tests
```bash
./scripts/run_tests.sh
./scripts/run_integration_tests.sh
```

### Test API endpoints
```bash
python scripts/tests/test_api.py
python scripts/tests/test_api_detailed.py
```

### Clean up project
```bash
./scripts/cleanup.sh
```

### Seed database with test data
```bash
python scripts/seed_data.py
```

## Notes

- All shell scripts should be executable (`chmod +x script.sh`)
- Python scripts can be run with `python scripts/script_name.py`
- Configuration files (`.yaml`, `.yml`) are used by their respective tools
- The `obsolete/` directory contains deprecated scripts that will be removed in future versions