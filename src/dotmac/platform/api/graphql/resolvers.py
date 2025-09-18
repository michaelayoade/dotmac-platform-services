"""GraphQL resolvers for the DotMac platform services."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any, AsyncIterator, Dict, List, Optional

from dotmac.platform.observability.unified_logging import get_logger
from dotmac.platform.auth.current_user import UserClaims
from dotmac.platform.auth.exceptions import AuthError

logger = get_logger(__name__)

try:
    import strawberry
    from strawberry.types import Info
except ImportError:
    strawberry = None
    Info = Any  # type: ignore

if strawberry:
    # Import platform services
    from dotmac.platform.auth.jwt_service import JWTService
    from dotmac.platform.auth.api_keys import APIKeyService
    from dotmac.platform.auth.session_manager import SessionManager
    from dotmac.platform.feature_flags.service import FeatureFlagService
    from dotmac.platform.secrets.manager import SecretsManager
    from dotmac.platform.observability.metrics.registry import MetricsRegistry


class AuthResolver:
    """Authentication and authorization resolvers."""

    @staticmethod
    async def get_current_user(info: Info) -> Optional["User"]:
        """Get current authenticated user."""
        try:
            # Extract user from JWT token in request headers
            request = info.context.get("request")
            if not request:
                return None

            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None

            token = auth_header.split(" ")[1]
            jwt_service = JWTService()
            claims = jwt_service.verify_token(token)

            user_claims = UserClaims.model_validate(claims)

            from ..schema import User
            return User(
                id=user_claims.user_id,
                username=user_claims.username,
                email=user_claims.email,
                full_name=user_claims.full_name,
                tenant_id=user_claims.tenant_id,
                roles=user_claims.roles,
                scopes=user_claims.scopes,
                is_active=True,
                created_at=datetime.now(UTC),  # Would come from user service
                last_login=datetime.now(UTC) if user_claims.issued_at else None
            )
        except Exception as e:
            logger.warning("Failed to get current user: %s", e)
            return None

    @staticmethod
    async def get_api_keys(info: Info) -> List["APIKey"]:
        """Get API keys for current user."""
        current_user = await AuthResolver.get_current_user(info)
        if not current_user:
            raise AuthError("Authentication required")

        try:
            api_key_service = APIKeyService()
            keys = await api_key_service.list_api_keys(current_user.id)

            from ..schema import APIKey
            return [
                APIKey(
                    id=key.id,
                    name=key.name,
                    prefix=key.prefix,
                    scopes=key.scopes,
                    expires_at=key.expires_at,
                    created_at=key.created_at,
                    last_used=key.last_used,
                    is_active=key.is_active
                )
                for key in keys
            ]
        except Exception as e:
            logger.error("Failed to get API keys: %s", e)
            return []

    @staticmethod
    async def get_sessions(info: Info, user_id: Optional[str] = None) -> List["Session"]:
        """Get user sessions."""
        current_user = await AuthResolver.get_current_user(info)
        if not current_user:
            raise AuthError("Authentication required")

        # Only allow users to see their own sessions unless admin
        target_user_id = user_id if "admin" in current_user.roles else current_user.id

        try:
            session_manager = SessionManager()
            sessions = await session_manager.get_user_sessions(target_user_id)

            from ..schema import Session
            return [
                Session(
                    id=session.session_id,
                    user_id=session.user_id,
                    ip_address=session.ip_address,
                    user_agent=session.user_agent,
                    created_at=session.created_at,
                    expires_at=session.expires_at,
                    is_active=session.is_active
                )
                for session in sessions
            ]
        except Exception as e:
            logger.error("Failed to get sessions: %s", e)
            return []

    @staticmethod
    async def create_api_key(
        info: Info,
        name: str,
        scopes: List[str],
        expires_at: Optional[datetime] = None
    ) -> "APIKey":
        """Create a new API key."""
        current_user = await AuthResolver.get_current_user(info)
        if not current_user:
            raise AuthError("Authentication required")

        try:
            api_key_service = APIKeyService()
            key = await api_key_service.create_api_key(
                user_id=current_user.id,
                name=name,
                scopes=scopes,
                expires_at=expires_at
            )

            from ..schema import APIKey
            return APIKey(
                id=key.id,
                name=key.name,
                prefix=key.prefix,
                scopes=key.scopes,
                expires_at=key.expires_at,
                created_at=key.created_at,
                last_used=None,
                is_active=True
            )
        except Exception as e:
            logger.error("Failed to create API key: %s", e)
            raise

    @staticmethod
    async def revoke_api_key(info: Info, api_key_id: str) -> bool:
        """Revoke an API key."""
        current_user = await AuthResolver.get_current_user(info)
        if not current_user:
            raise AuthError("Authentication required")

        try:
            api_key_service = APIKeyService()
            await api_key_service.revoke_api_key(api_key_id, current_user.id)
            return True
        except Exception as e:
            logger.error("Failed to revoke API key: %s", e)
            return False

    @staticmethod
    async def invalidate_session(info: Info, session_id: str) -> bool:
        """Invalidate a user session."""
        current_user = await AuthResolver.get_current_user(info)
        if not current_user:
            raise AuthError("Authentication required")

        try:
            session_manager = SessionManager()
            await session_manager.invalidate_session(session_id, current_user.id)
            return True
        except Exception as e:
            logger.error("Failed to invalidate session: %s", e)
            return False


class FeatureFlagResolver:
    """Feature flag resolvers."""

    @staticmethod
    async def get_feature_flags(
        info: Info,
        first: Optional[int] = 50,
        after: Optional[str] = None
    ) -> "FeatureFlagsConnection":
        """Get feature flags with pagination."""
        try:
            feature_service = FeatureFlagService()
            flags = await feature_service.list_flags(limit=first, cursor=after)

            from ..schema import FeatureFlag, FeatureFlagsConnection, PageInfo
            flag_objects = [
                FeatureFlag(
                    key=flag.key,
                    name=flag.name,
                    description=flag.description,
                    enabled=flag.enabled,
                    strategy=flag.strategy,
                    config=flag.config,
                    created_at=flag.created_at,
                    updated_at=flag.updated_at,
                    created_by=flag.created_by
                )
                for flag in flags
            ]

            return FeatureFlagsConnection(
                nodes=flag_objects,
                page_info=PageInfo(
                    has_next_page=len(flag_objects) == first,
                    has_previous_page=bool(after),
                    start_cursor=flag_objects[0].key if flag_objects else None,
                    end_cursor=flag_objects[-1].key if flag_objects else None,
                    total_count=len(flag_objects)
                )
            )
        except Exception as e:
            logger.error("Failed to get feature flags: %s", e)
            from ..schema import FeatureFlagsConnection, PageInfo
            return FeatureFlagsConnection(
                nodes=[],
                page_info=PageInfo(
                    has_next_page=False,
                    has_previous_page=False,
                    start_cursor=None,
                    end_cursor=None,
                    total_count=0
                )
            )

    @staticmethod
    async def get_feature_flag(info: Info, key: str) -> Optional["FeatureFlag"]:
        """Get a specific feature flag."""
        try:
            feature_service = FeatureFlagService()
            flag = await feature_service.get_flag(key)
            if not flag:
                return None

            from ..schema import FeatureFlag
            return FeatureFlag(
                key=flag.key,
                name=flag.name,
                description=flag.description,
                enabled=flag.enabled,
                strategy=flag.strategy,
                config=flag.config,
                created_at=flag.created_at,
                updated_at=flag.updated_at,
                created_by=flag.created_by
            )
        except Exception as e:
            logger.error("Failed to get feature flag %s: %s", key, e)
            return None

    @staticmethod
    async def evaluate_flags(
        info: Info,
        flags: List[str],
        context: Dict[str, Any]
    ) -> List["FeatureFlagEvaluation"]:
        """Evaluate feature flags."""
        current_user = await AuthResolver.get_current_user(info)
        evaluation_context = {
            "user_id": current_user.id if current_user else None,
            "tenant_id": current_user.tenant_id if current_user else None,
            **context
        }

        try:
            feature_service = FeatureFlagService()
            evaluations = []

            for flag_key in flags:
                result = await feature_service.evaluate_flag(flag_key, evaluation_context)

                from ..schema import FeatureFlagEvaluation
                evaluations.append(
                    FeatureFlagEvaluation(
                        flag_key=flag_key,
                        enabled=result.enabled,
                        variant=result.variant,
                        reason=result.reason,
                        context=evaluation_context
                    )
                )

            return evaluations
        except Exception as e:
            logger.error("Failed to evaluate flags: %s", e)
            return []

    @staticmethod
    async def upsert_feature_flag(info: Info, input: "FeatureFlagInput") -> "FeatureFlag":
        """Create or update a feature flag."""
        current_user = await AuthResolver.get_current_user(info)
        if not current_user:
            raise AuthError("Authentication required")

        try:
            feature_service = FeatureFlagService()
            flag = await feature_service.upsert_flag(
                key=input.key,
                name=input.name,
                description=input.description,
                enabled=input.enabled,
                strategy=input.strategy,
                config=input.config,
                created_by=current_user.id
            )

            from ..schema import FeatureFlag
            return FeatureFlag(
                key=flag.key,
                name=flag.name,
                description=flag.description,
                enabled=flag.enabled,
                strategy=flag.strategy,
                config=flag.config,
                created_at=flag.created_at,
                updated_at=flag.updated_at,
                created_by=flag.created_by
            )
        except Exception as e:
            logger.error("Failed to upsert feature flag: %s", e)
            raise

    @staticmethod
    async def delete_feature_flag(info: Info, key: str) -> bool:
        """Delete a feature flag."""
        current_user = await AuthResolver.get_current_user(info)
        if not current_user:
            raise AuthError("Authentication required")

        try:
            feature_service = FeatureFlagService()
            await feature_service.delete_flag(key)
            return True
        except Exception as e:
            logger.error("Failed to delete feature flag %s: %s", key, e)
            return False

    @staticmethod
    async def toggle_feature_flag(info: Info, key: str, enabled: bool) -> "FeatureFlag":
        """Toggle a feature flag."""
        current_user = await AuthResolver.get_current_user(info)
        if not current_user:
            raise AuthError("Authentication required")

        try:
            feature_service = FeatureFlagService()
            flag = await feature_service.toggle_flag(key, enabled)

            from ..schema import FeatureFlag
            return FeatureFlag(
                key=flag.key,
                name=flag.name,
                description=flag.description,
                enabled=flag.enabled,
                strategy=flag.strategy,
                config=flag.config,
                created_at=flag.created_at,
                updated_at=flag.updated_at,
                created_by=flag.created_by
            )
        except Exception as e:
            logger.error("Failed to toggle feature flag %s: %s", key, e)
            raise


class SecretsResolver:
    """Secrets management resolvers."""

    @staticmethod
    async def list_secrets(info: Info, path_prefix: Optional[str] = None) -> List["SecretMetadata"]:
        """List secret metadata."""
        current_user = await AuthResolver.get_current_user(info)
        if not current_user:
            raise AuthError("Authentication required")

        try:
            secrets_manager = SecretsManager()
            secrets = await secrets_manager.list_secrets(path_prefix or "")

            from ..schema import SecretMetadata
            return [
                SecretMetadata(
                    path=secret.path,
                    version=secret.version,
                    created_at=secret.created_at,
                    updated_at=secret.updated_at,
                    tags=secret.metadata.get("tags", {}),
                    description=secret.metadata.get("description")
                )
                for secret in secrets
            ]
        except Exception as e:
            logger.error("Failed to list secrets: %s", e)
            return []

    @staticmethod
    async def get_secret_history(info: Info, path: str) -> List["SecretHistory"]:
        """Get secret version history."""
        current_user = await AuthResolver.get_current_user(info)
        if not current_user:
            raise AuthError("Authentication required")

        try:
            secrets_manager = SecretsManager()
            history = await secrets_manager.get_secret_history(path)

            from ..schema import SecretHistory
            return [
                SecretHistory(
                    version=entry.version,
                    created_at=entry.created_at,
                    created_by=entry.created_by,
                    description=entry.description
                )
                for entry in history
            ]
        except Exception as e:
            logger.error("Failed to get secret history for %s: %s", path, e)
            return []


class ObservabilityResolver:
    """Observability resolvers."""

    @staticmethod
    async def get_metrics(info: Info, filter: Optional["MetricsFilter"] = None) -> List["Metric"]:
        """Get system metrics."""
        try:
            metrics_registry = MetricsRegistry()
            metrics = await metrics_registry.get_metrics(
                name_pattern=filter.name_pattern if filter else None,
                labels=filter.labels if filter else None,
                start_time=filter.start_time if filter else None,
                end_time=filter.end_time if filter else None
            )

            from ..schema import Metric, MetricValue
            metric_objects = []
            for metric in metrics:
                recent_values = [
                    MetricValue(
                        timestamp=value.timestamp,
                        value=value.value,
                        labels=value.labels
                    )
                    for value in metric.recent_values
                ]

                metric_objects.append(
                    Metric(
                        name=metric.name,
                        description=metric.description,
                        type=metric.type,
                        unit=metric.unit,
                        recent_values=recent_values
                    )
                )

            return metric_objects
        except Exception as e:
            logger.error("Failed to get metrics: %s", e)
            return []

    @staticmethod
    async def get_health_checks(info: Info) -> List["HealthCheck"]:
        """Get service health checks."""
        try:
            # Mock health checks - integrate with actual health check system
            from ..schema import HealthCheck
            return [
                HealthCheck(
                    service_name="auth-service",
                    status="healthy",
                    message="All checks passed",
                    last_check=datetime.now(UTC),
                    response_time_ms=25.5
                ),
                HealthCheck(
                    service_name="secrets-service",
                    status="healthy",
                    message="Vault connection OK",
                    last_check=datetime.now(UTC),
                    response_time_ms=42.1
                ),
                HealthCheck(
                    service_name="database",
                    status="healthy",
                    message="Connection pool OK",
                    last_check=datetime.now(UTC),
                    response_time_ms=15.3
                )
            ]
        except Exception as e:
            logger.error("Failed to get health checks: %s", e)
            return []

    @staticmethod
    async def get_traces(
        info: Info,
        service_name: Optional[str] = None,
        limit: Optional[int] = 100
    ) -> List["TraceSpan"]:
        """Get recent traces."""
        try:
            # Mock traces - integrate with actual tracing system
            from ..schema import TraceSpan
            return [
                TraceSpan(
                    trace_id="abc123def456",
                    span_id="span001",
                    parent_span_id=None,
                    operation_name="POST /api/auth/login",
                    start_time=datetime.now(UTC),
                    end_time=datetime.now(UTC),
                    duration_ms=125.5,
                    status="ok",
                    tags={"http.method": "POST", "http.status_code": "200"}
                )
            ]
        except Exception as e:
            logger.error("Failed to get traces: %s", e)
            return []

    @staticmethod
    async def stream_metrics(
        info: Info,
        metric_names: List[str]
    ) -> AsyncIterator["MetricValue"]:
        """Stream metric updates."""
        # Mock streaming metrics
        import asyncio
        while True:
            try:
                from ..schema import MetricValue
                yield MetricValue(
                    timestamp=datetime.now(UTC),
                    value=42.0,
                    labels={"service": "api-gateway"}
                )
                await asyncio.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logger.error("Error streaming metrics: %s", e)
                break


class AuditTrailResolver:
    """Audit trail resolvers."""

    @staticmethod
    async def search_events(
        info: Info,
        filter: Optional["AuditEventFilter"] = None,
        first: Optional[int] = 50,
        after: Optional[str] = None
    ) -> "AuditEventsConnection":
        """Search audit events."""
        try:
            # Mock audit events - integrate with actual audit service
            from ..schema import AuditEvent, AuditEventsConnection, PageInfo, AuditCategory, AuditLevel
            events = [
                AuditEvent(
                    id="audit001",
                    timestamp=datetime.now(UTC),
                    category=AuditCategory.AUTHENTICATION,
                    level=AuditLevel.INFO,
                    action="login",
                    resource="user",
                    actor="user123",
                    tenant_id="tenant001",
                    ip_address="192.168.1.100",
                    user_agent="Mozilla/5.0...",
                    details={"method": "password"},
                    outcome="success"
                )
            ]

            return AuditEventsConnection(
                nodes=events,
                page_info=PageInfo(
                    has_next_page=False,
                    has_previous_page=False,
                    start_cursor="audit001",
                    end_cursor="audit001",
                    total_count=1
                )
            )
        except Exception as e:
            logger.error("Failed to search audit events: %s", e)
            from ..schema import AuditEventsConnection, PageInfo
            return AuditEventsConnection(
                nodes=[],
                page_info=PageInfo(
                    has_next_page=False,
                    has_previous_page=False,
                    start_cursor=None,
                    end_cursor=None,
                    total_count=0
                )
            )

    @staticmethod
    async def get_event(info: Info, event_id: str) -> Optional["AuditEvent"]:
        """Get audit event by ID."""
        try:
            # Mock single event - integrate with actual audit service
            from ..schema import AuditEvent, AuditCategory, AuditLevel
            return AuditEvent(
                id=event_id,
                timestamp=datetime.now(UTC),
                category=AuditCategory.AUTHENTICATION,
                level=AuditLevel.INFO,
                action="login",
                resource="user",
                actor="user123",
                tenant_id="tenant001",
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0...",
                details={"method": "password"},
                outcome="success"
            )
        except Exception as e:
            logger.error("Failed to get audit event %s: %s", event_id, e)
            return None

    @staticmethod
    async def log_event(
        info: Info,
        category: "AuditCategory",
        level: "AuditLevel",
        action: str,
        resource: str,
        details: Dict[str, Any]
    ) -> "AuditEvent":
        """Log a new audit event."""
        current_user = await AuthResolver.get_current_user(info)
        if not current_user:
            raise AuthError("Authentication required")

        try:
            # Mock event creation - integrate with actual audit service
            from ..schema import AuditEvent
            return AuditEvent(
                id=f"audit_{datetime.now(UTC).timestamp()}",
                timestamp=datetime.now(UTC),
                category=category,
                level=level,
                action=action,
                resource=resource,
                actor=current_user.id,
                tenant_id=current_user.tenant_id,
                ip_address=None,  # Extract from request
                user_agent=None,  # Extract from request
                details=details,
                outcome="success"
            )
        except Exception as e:
            logger.error("Failed to log audit event: %s", e)
            raise

    @staticmethod
    async def stream_events(
        info: Info,
        filter: Optional["AuditEventFilter"] = None
    ) -> AsyncIterator["AuditEvent"]:
        """Stream audit events in real-time."""
        # Mock streaming events
        import asyncio
        while True:
            try:
                from ..schema import AuditEvent, AuditCategory, AuditLevel
                yield AuditEvent(
                    id=f"stream_{datetime.now(UTC).timestamp()}",
                    timestamp=datetime.now(UTC),
                    category=AuditCategory.SYSTEM_CHANGE,
                    level=AuditLevel.INFO,
                    action="config_update",
                    resource="system",
                    actor="system",
                    tenant_id=None,
                    ip_address=None,
                    user_agent=None,
                    details={"component": "feature_flags"},
                    outcome="success"
                )
                await asyncio.sleep(10)  # New event every 10 seconds
            except Exception as e:
                logger.error("Error streaming audit events: %s", e)
                break


class ServiceRegistryResolver:
    """Service registry resolvers."""

    @staticmethod
    async def get_services(
        info: Info,
        status: Optional["ServiceStatus"] = None,
        first: Optional[int] = 50,
        after: Optional[str] = None
    ) -> "ServiceInstancesConnection":
        """Get registered services."""
        try:
            # Mock services - integrate with actual service registry
            from ..schema import ServiceInstance, ServiceInstancesConnection, PageInfo, ServiceStatus
            services = [
                ServiceInstance(
                    id="service001",
                    name="auth-service",
                    version="1.0.0",
                    status=ServiceStatus.HEALTHY,
                    endpoint="http://auth-service:8080",
                    health_check_url="http://auth-service:8080/health",
                    tags={"environment": "production", "team": "platform"},
                    metadata={"instances": 3, "load_balancer": "round_robin"},
                    registered_at=datetime.now(UTC),
                    last_heartbeat=datetime.now(UTC)
                )
            ]

            return ServiceInstancesConnection(
                nodes=services,
                page_info=PageInfo(
                    has_next_page=False,
                    has_previous_page=False,
                    start_cursor="service001",
                    end_cursor="service001",
                    total_count=1
                )
            )
        except Exception as e:
            logger.error("Failed to get services: %s", e)
            from ..schema import ServiceInstancesConnection, PageInfo
            return ServiceInstancesConnection(
                nodes=[],
                page_info=PageInfo(
                    has_next_page=False,
                    has_previous_page=False,
                    start_cursor=None,
                    end_cursor=None,
                    total_count=0
                )
            )

    @staticmethod
    async def get_service(info: Info, service_id: str) -> Optional["ServiceInstance"]:
        """Get service by ID."""
        try:
            from ..schema import ServiceInstance, ServiceStatus
            return ServiceInstance(
                id=service_id,
                name="auth-service",
                version="1.0.0",
                status=ServiceStatus.HEALTHY,
                endpoint="http://auth-service:8080",
                health_check_url="http://auth-service:8080/health",
                tags={"environment": "production", "team": "platform"},
                metadata={"instances": 3, "load_balancer": "round_robin"},
                registered_at=datetime.now(UTC),
                last_heartbeat=datetime.now(UTC)
            )
        except Exception as e:
            logger.error("Failed to get service %s: %s", service_id, e)
            return None

    @staticmethod
    async def stream_health(info: Info) -> AsyncIterator["HealthCheck"]:
        """Stream service health updates."""
        import asyncio
        while True:
            try:
                from ..schema import HealthCheck
                yield HealthCheck(
                    service_name="auth-service",
                    status="healthy",
                    message="All systems operational",
                    last_check=datetime.now(UTC),
                    response_time_ms=28.3
                )
                await asyncio.sleep(30)  # Health check every 30 seconds
            except Exception as e:
                logger.error("Error streaming health updates: %s", e)
                break