"""
Main FastAPI application entry point for DotMac Platform Services.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import os
from typing import Dict, Any

# Import routers and configurations
from dotmac.platform.api_gateway import create_api_gateway
from dotmac.platform.telemetry import setup_telemetry
from dotmac.platform.settings import settings
from dotmac.platform.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events."""
    # Startup
    print("Starting DotMac Platform Services...")

    # Initialize database
    await init_db()

    # Setup telemetry if enabled
    if settings.observability.otel_enabled:
        setup_telemetry(app)

    yield

    # Shutdown
    print("Shutting down DotMac Platform Services...")
    # Cleanup resources here if needed


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""

    # Use centralized settings
    config = settings

    # Create FastAPI app
    app = FastAPI(
        title="DotMac Platform Services",
        description="Unified platform services providing auth, secrets, and observability",
        version=os.getenv("APP_VERSION", "1.0.0"),
        lifespan=lifespan,
        docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
        redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
    )

    # Configure CORS
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Mount API Gateway
    gateway = create_api_gateway(config)
    app.mount("/api", gateway)

    # Health check endpoint
    @app.get("/health")
    async def health_check() -> Dict[str, Any]:
        """Health check endpoint for monitoring."""
        return {
            "status": "healthy",
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "environment": os.getenv("ENVIRONMENT", "development"),
        }

    # Readiness check endpoint
    @app.get("/ready")
    async def readiness_check() -> Dict[str, Any]:
        """Readiness check endpoint for Kubernetes."""
        # Add checks for database, redis, etc.
        return {
            "status": "ready",
            "checks": {
                "database": "ok",
                "cache": "ok",
                "secrets": "ok",
            }
        }

    # Metrics endpoint (if Prometheus enabled)
    if os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true":
        from prometheus_client import make_asgi_app
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)

    return app


# Create application instance
app = create_application()


# For development server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "dotmac.platform.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    )