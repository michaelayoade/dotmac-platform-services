"""
Main FastAPI application entry point for DotMac Platform Services.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from dotmac.platform.db import init_db
from dotmac.platform.health_checks import HealthChecker, ensure_infrastructure_running
from dotmac.platform.routers import get_api_info, register_routers
from dotmac.platform.secrets import load_secrets_from_vault_sync
from dotmac.platform.settings import settings
from dotmac.platform.telemetry import setup_telemetry


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events."""
    # Startup
    print("Starting DotMac Platform Services...")

    # Check service dependencies
    checker = HealthChecker()
    all_healthy, checks = checker.run_all_checks()

    print("\n" + "=" * 60)
    print("Service Dependency Health Checks")
    print("=" * 60)
    for check in checks:
        icon = "✅" if check.is_healthy else "❌" if check.required else "⚠️"
        print(f"{icon} {check.name}: {check.status.value} - {check.message}")
    print("=" * 60 + "\n")

    # Fail fast in production if required services are missing
    if not all_healthy:
        failed_required = [c.name for c in checks if c.required and not c.is_healthy]
        if failed_required and settings.environment == "production":
            raise RuntimeError(f"Required services not available: {', '.join(failed_required)}")

    # Load secrets from Vault/OpenBao if configured
    try:
        load_secrets_from_vault_sync()
        print("✅ Secrets loaded from Vault/OpenBao")
    except Exception as e:
        print(f"⚠️  Failed to load secrets from Vault: {e}")
        # Continue with default values in development, fail in production
        if settings.environment == "production":
            raise

    # Initialize database
    init_db()
    print("✅ Database initialized")

    # Setup telemetry (includes structlog configuration)
    setup_telemetry(app)
    print("✅ Telemetry and structured logging configured")

    yield

    # Shutdown
    print("Shutting down DotMac Platform Services...")
    # Cleanup resources here if needed


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Create FastAPI app
    app = FastAPI(
        title="DotMac Platform Services",
        description="Unified platform services providing auth, secrets, and observability",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )

    # Configure CORS
    if settings.cors.enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors.origins,
            allow_credentials=settings.cors.credentials,
            allow_methods=settings.cors.methods,
            allow_headers=settings.cors.headers,
            max_age=settings.cors.max_age,
        )

    # Add GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Register all API routers
    register_routers(app)

    # Health check endpoint (public - no auth required)
    @app.get("/health")
    async def health_check() -> Dict[str, Any]:
        """Health check endpoint for monitoring."""
        return {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
        }

    # Liveness check endpoint (public - no auth required)
    @app.get("/health/live")
    async def liveness_check() -> Dict[str, Any]:
        """Liveness check endpoint for Kubernetes."""
        return {
            "status": "alive",
            "version": settings.app_version,
            "environment": settings.environment,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # Readiness check endpoint (public - no auth required)
    @app.get("/health/ready")
    async def readiness_check() -> Dict[str, Any]:
        """Readiness check endpoint for Kubernetes."""
        checker = HealthChecker()
        summary = checker.get_summary()

        return {
            "status": "ready" if summary["healthy"] else "not ready",
            "healthy": summary["healthy"],
            "services": summary["services"],
            "failed_services": summary["failed_services"],
            "timestamp": datetime.utcnow().isoformat(),
        }

    # Keep /ready for backwards compatibility
    @app.get("/ready")
    async def ready_check() -> Dict[str, Any]:
        """Readiness check endpoint (deprecated, use /health/ready)."""
        return await readiness_check()

    # API info endpoint (public - shows available endpoints)
    @app.get("/api")
    async def api_info() -> Dict[str, Any]:
        """Get information about available API endpoints."""
        return get_api_info()

    # Metrics endpoint (if metrics enabled)
    if settings.observability.enable_metrics:
        from prometheus_client import make_asgi_app

        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)

    return app


# Create application instance
app = create_application()


# For development server
if __name__ == "__main__":
    import uvicorn

    # Show infrastructure requirements
    ensure_infrastructure_running()

    uvicorn.run(
        "dotmac.platform.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.observability.log_level.value.lower(),
    )
