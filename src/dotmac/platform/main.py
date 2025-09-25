"""
Main FastAPI application entry point for DotMac Platform Services.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.responses import Response

from dotmac.platform.db import init_db
from dotmac.platform.health_checks import HealthChecker, ensure_infrastructure_running
from dotmac.platform.rate_limiting import limiter
from dotmac.platform.routers import get_api_info, register_routers
from dotmac.platform.secrets import load_secrets_from_vault_sync
from dotmac.platform.settings import settings
from dotmac.platform.telemetry import setup_telemetry


def rate_limit_handler(request: Request, exc: Exception) -> Response:
    """Handle rate limit exceeded exceptions with proper typing."""
    # Cast to RateLimitExceeded since we know it will be that type when called
    return _rate_limit_exceeded_handler(request, exc)  # type: ignore


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle events."""
    # Setup telemetry first to enable structured logging
    setup_telemetry(app)

    # Get structured logger after telemetry setup
    import structlog
    logger = structlog.get_logger(__name__)

    # Structured startup event
    logger.info(
        "service.startup.begin",
        service="dotmac-platform",
        version=settings.app_version,
        environment=settings.environment
    )

    # Check service dependencies with structured logging
    checker = HealthChecker()
    all_healthy, checks = checker.run_all_checks()

    # Log each dependency check as structured events
    for check in checks:
        logger.info(
            "service.dependency.check",
            dependency=check.name,
            status=check.status.value,
            healthy=check.is_healthy,
            required=check.required,
            message=check.message
        )

    # Summary for human-readable console output (keep minimal print for deployment visibility)
    print(f"🚀 DotMac Platform Services starting (v{settings.app_version})")
    failed_services = [c.name for c in checks if c.required and not c.is_healthy]
    if failed_services:
        print(f"❌ Required services unavailable: {', '.join(failed_services)}")
    elif not all_healthy:
        optional_failed = [c.name for c in checks if not c.required and not c.is_healthy]
        print(f"⚠️  Optional services unavailable: {', '.join(optional_failed)}")
    else:
        print("✅ All service dependencies healthy")

    # Fail fast in production if required services are missing
    if not all_healthy:
        if failed_services and settings.environment == "production":
            logger.error(
                "service.startup.failed",
                failed_services=failed_services,
                environment=settings.environment
            )
            raise RuntimeError(f"Required services unavailable: {failed_services}")
        else:
            logger.warning(
                "service.startup.degraded",
                optional_failed_services=[c.name for c in checks if not c.required and not c.is_healthy]
            )

    # Load secrets from Vault/OpenBao if configured
    try:
        load_secrets_from_vault_sync()
        logger.info("secrets.load.success", source="vault")
        print("✅ Secrets loaded from Vault/OpenBao")
    except Exception as e:
        logger.warning("secrets.load.failed", source="vault", error=str(e))
        print(f"⚠️  Using default secrets (Vault unavailable: {e})")
        # Continue with default values in development, fail in production
        if settings.environment == "production":
            logger.error("secrets.load.production_failure", error=str(e))
            raise

    # Initialize database
    try:
        init_db()
        logger.info("database.init.success")
        print("✅ Database initialized")
    except Exception as e:
        logger.error("database.init.failed", error=str(e))
        raise

    logger.info("service.startup.complete", healthy=all_healthy)
    print("🎉 Startup complete - service ready")

    yield

    # Shutdown with structured logging
    logger.info("service.shutdown.begin")
    print("👋 Shutting down DotMac Platform Services...")

    # Cleanup resources here if needed

    logger.info("service.shutdown.complete")
    print("✅ Shutdown complete")


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

    # Add rate limiting support
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

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
