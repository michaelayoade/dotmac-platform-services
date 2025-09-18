"""
Generic observability integration for DotMac applications.

This module wires together OpenTelemetry, the metrics registry, optional
tenant-scoped business metrics, service-to-service auth, and optional
edge validation in a way that is reusable across applications.

Application-specific behavior is injected via hooks.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI

from dotmac.platform.observability.unified_logging import get_logger

try:
    # Platform observability surface
    from dotmac.platform.observability import (
        create_default_config,
        initialize_metrics_registry,
        initialize_otel,
        initialize_tenant_metrics,
    )
except Exception as e:  # pragma: no cover - import guard
    raise ImportError(f"dotmac.platform.observability not available: {e}")

try:
    # Service-to-service authentication
    from dotmac.platform.auth import create_jwt_service_from_config
    from dotmac.platform.auth.edge_validation import EdgeJWTValidator
    from dotmac.platform.auth.service_auth import create_service_token_manager
except Exception:  # pragma: no cover - import guard
    # Auth is optional for observability
    create_service_token_manager = None
    EdgeJWTValidator = None
    create_jwt_service_from_config = None

try:
    # Tenant identity resolver
    from dotmac.platform.tenant import TenantIdentityResolver
except Exception as e:  # pragma: no cover - import guard
    raise ImportError(f"dotmac.platform.tenant not available: {e}")

try:
    # Application configuration types
    from dotmac.platform.config.base import BaseConfig as PlatformConfig
except Exception as e:  # pragma: no cover - import guard
    raise ImportError(f"dotmac.platform.config.base not available: {e}")

logger = get_logger(__name__)

@dataclass
class ObservabilityHooks:
    """Hooks for injecting application-specific observability behavior."""

    configure_tenant_patterns: Callable[[TenantIdentityResolver, PlatformConfig], None] | None = (
        None
    )
    configure_route_sensitivity: Callable[[EdgeJWTValidator, PlatformConfig], None] | None = None
    register_business_metrics: Callable[[Any, PlatformConfig], None] | None = None
    register_service_capabilities: Callable[[Any, str, str, str, PlatformConfig], None] | None = (
        None
    )
    customize_resource_attributes: (
        Callable[[dict[str, str], PlatformConfig], dict[str, str]] | None
    ) = None

async def setup_observability(
    app: FastAPI,
    platform_config: PlatformConfig,
    *,
    enable_business_slos: bool = True,
    hooks: ObservabilityHooks | None = None,
) -> dict[str, Any]:
    """Set up observability for a DotMac application.

    - Initializes OpenTelemetry with environment-aware exporters
    - Creates a metrics registry and (optionally) tenant metrics
    - Configures service-to-service authentication token manager
    - Creates tenant identity resolver and edge JWT validator
    - Optionally registers business metrics and service capabilities via hooks

    Returns a mapping of components and stores them on app.state.
    """
    hooks = hooks or ObservabilityHooks()

    # Determine environment
    environment = os.getenv("ENVIRONMENT", "production").lower()
    service_version = os.getenv("APP_VERSION", "1.0.0")
    service_name = _get_service_name(platform_config)

    # Select exporters by environment
    tracing_exporters, metrics_exporters = _select_exporters(environment)

    # Resource attributes
    resource_attrs = _get_resource_attributes(platform_config)
    if hooks.customize_resource_attributes:
        try:
            resource_attrs = (
                hooks.customize_resource_attributes(resource_attrs, platform_config)
                or resource_attrs
            )
        except Exception as e:
            logger.warning(f"customize_resource_attributes hook failed: {e}")

    # 1) Initialize OpenTelemetry
    otel_config = create_default_config(
        service_name=service_name,
        environment=environment,
        service_version=service_version,
        custom_resource_attributes=resource_attrs,
        tracing_exporters=tracing_exporters,
        metrics_exporters=metrics_exporters,
    )
    otel_bootstrap = initialize_otel(otel_config)

    # 2) Metrics registry (+optional tenant metrics)
    metrics_registry = initialize_metrics_registry(service_name)
    if otel_bootstrap and hasattr(otel_bootstrap, "get_meter"):
        meter = otel_bootstrap.get_meter()
        if meter:
            try:
                metrics_registry.set_otel_meter(meter)
            except Exception as e:
                logger.warning(f"Failed to connect OTEL meter to metrics registry: {e}")

    tenant_metrics = None
    if enable_business_slos:
        try:
            tenant_metrics = initialize_tenant_metrics(
                service_name=service_name,
                metrics_registry=metrics_registry,
                enable_dashboards=True,
                enable_slo_monitoring=True,
            )
            if hooks.register_business_metrics:
                hooks.register_business_metrics(tenant_metrics, platform_config)
        except Exception as e:
            logger.warning(f"Tenant metrics initialization failed: {e}")

    # 3) Service-to-service authentication
    service_signing_secret = os.getenv(
        "SERVICE_SIGNING_SECRET", "dev-secret-key-change-in-production"
    )
    service_token_manager = None
    if create_service_token_manager:
        try:
            service_token_manager = create_service_token_manager(
                signing_secret=service_signing_secret
            )
        except Exception as e:
            logger.warning(f"Service token manager initialization failed: {e}")
    if hooks.register_service_capabilities:
        try:
            hooks.register_service_capabilities(
                service_token_manager, service_name, service_version, environment, platform_config
            )
        except Exception as e:
            logger.warning(f"register_service_capabilities hook failed: {e}")

    # 4) Tenant identity + edge validation
    tenant_resolver = TenantIdentityResolver()
    if hooks.configure_tenant_patterns:
        try:
            hooks.configure_tenant_patterns(tenant_resolver, platform_config)
        except Exception as e:
            logger.warning(f"configure_tenant_patterns hook failed: {e}")

    jwt_secret = os.getenv("JWT_SECRET", "dev-jwt-secret-change-in-production")
    if not jwt_secret or jwt_secret == "your-jwt-secret-change-this-in-production":
        jwt_secret = "dev-jwt-secret-change-in-production"
    try:
        jwt_service = create_jwt_service_from_config({"secret": jwt_secret, "algorithm": "HS256"})
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"Failed to initialize JWT service for edge validation: {e}")
    edge_validator = EdgeJWTValidator(jwt_service=jwt_service, tenant_resolver=tenant_resolver)
    if hooks.configure_route_sensitivity:
        try:
            hooks.configure_route_sensitivity(edge_validator, platform_config)
        except Exception as e:
            logger.warning(f"configure_route_sensitivity hook failed: {e}")

    components = {
        "otel_bootstrap": otel_bootstrap,
        "metrics_registry": metrics_registry,
        "tenant_metrics": tenant_metrics,
        "service_token_manager": service_token_manager,
        "tenant_resolver": tenant_resolver,
        "edge_validator": edge_validator,
        "environment": environment,
        "service_name": service_name,
        "service_version": service_version,
    }

    # Store on app state
    for key, value in components.items():
        setattr(app.state, key, value)

    logger.info(
        "Observability initialized (service=%s, env=%s, version=%s)",
        service_name,
        environment,
        service_version,
    )

    return components

def _select_exporters(environment: str) -> tuple[list[str], list[str]]:
    if environment == "development":
        return ["console"], ["console"]
    if environment == "staging":
        return ["otlp", "console"], ["otlp"]
    return ["otlp"], ["otlp"]  # production default

def _get_service_name(platform_config: PlatformConfig) -> str:
    # Prefer explicit platform/service name if available
    service_name = getattr(platform_config, "platform_name", None) or getattr(
        platform_config, "app_name", "dotmac-service"
    )

    context = getattr(platform_config, "deployment_context", None)
    if not context:
        return service_name

    mode = getattr(context, "mode", None)
    mode_value = getattr(mode, "value", mode)
    if isinstance(mode_value, str) and mode_value.replace("-", "_").lower() == "tenant_container":
        tenant_id = getattr(context, "tenant_id", "unknown")
        return f"{service_name}-{tenant_id}"

    return service_name

def _get_resource_attributes(platform_config: PlatformConfig) -> dict[str, str]:
    attributes: dict[str, str] = {
        "service.namespace": "dotmac",
        "deployment.environment": getattr(
            platform_config, "environment", os.getenv("ENVIRONMENT", "production")
        ),
    }
    ctx = getattr(platform_config, "deployment_context", None)
    if ctx:
        mode = getattr(ctx, "mode", None)
        attributes["deployment.mode"] = getattr(mode, "value", str(mode))
        if getattr(ctx, "tenant_id", None):
            attributes["tenant.id"] = str(ctx.tenant_id)
    return attributes
