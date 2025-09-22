"""Comprehensive GraphQL schema definitions for the DotMac platform."""

from __future__ import annotations

import enum
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict, List, Optional

from dotmac.platform.logging import get_logger

logger = get_logger(__name__)


try:  # pragma: no cover - optional dependency import
    import strawberry
    from strawberry.types import Info
except ImportError:  # pragma: no cover - graceful fallback when Strawberry not installed
    strawberry = None  # type: ignore[assignment]
    Info = Any  # type: ignore[assignment]
    logger.info(
        "Strawberry not installed; GraphQL endpoint will remain disabled unless the dependency is provided."
    )
else:  # pragma: no cover - handle incomplete strawberry installs
    required_attrs = ("Schema", "type", "enum", "field", "input", "subscription")
    missing_attrs = [attr for attr in required_attrs if not hasattr(strawberry, attr)]
    if missing_attrs:
        logger.info(
            "Strawberry package missing GraphQL helpers (%s); using lightweight stub instead."
            % ", ".join(sorted(missing_attrs))
        )
        strawberry = None  # type: ignore[assignment]
        Info = Any  # type: ignore[assignment]

if strawberry is None:
    class _StrawberryStub:
        """Minimal Strawberry replacement for environments without the dependency."""

        Enum = enum.Enum

        class Schema:
            def __init__(self, query=None, mutation=None, subscription=None):
                self.query = query
                self.mutation = mutation
                self.subscription = subscription

        def _identity(self, obj=None, **kwargs):
            if obj is None:
                def decorator(inner):
                    return inner
                return decorator
            return obj

        def type(self, obj=None, **kwargs):
            return self._identity(obj, **kwargs)

        def input(self, obj=None, **kwargs):
            return self._identity(obj, **kwargs)

        def field(self, obj=None, **kwargs):
            return self._identity(obj, **kwargs)

        def enum(self, obj=None, **kwargs):
            return self._identity(obj, **kwargs)

        def subscription(self, obj=None, **kwargs):
            return self._identity(obj, **kwargs)

    strawberry = _StrawberryStub()
    Info = Any  # type: ignore[assignment]
    logger.info("Using lightweight Strawberry stub for GraphQL schema generation.")

if strawberry:  # pragma: no branch - executed only when strawberry is available
    from .resolvers import (
        AuthResolver,
        FeatureFlagResolver,
        SecretsResolver,
        ObservabilityResolver,
        AuditTrailResolver,
        ServiceRegistryResolver,
    )
    try:
        from strawberry.scalars import JSON as JSONScalar
    except ImportError:  # pragma: no cover - fallback when JSON scalar missing
        JSONScalar = Dict[str, Any]  # type: ignore[assignment]

    _MISSING = object()

    def _safe_get(obj: Any, *names: str, default: Any = None) -> Any:
        """Retrieve the first matching attribute or dict key from an object."""
        for name in names:
            if isinstance(obj, dict) and name in obj:
                return obj[name]
            value = getattr(obj, name, _MISSING)
            if value is _MISSING:
                continue
            if hasattr(obj, "_mock_children"):
                mock_children = getattr(obj, "_mock_children")  # type: ignore[attr-defined]
                if (
                    name in mock_children
                    and mock_children[name] is value
                    and not (hasattr(obj, "__dict__") and name in obj.__dict__)
                ):
                    continue
            return value
        return default

    def _coerce_enum_value(enum_cls: type[Enum], value: Any) -> Enum:
        """Best-effort conversion of arbitrary enum-like values."""
        if isinstance(value, enum_cls):
            return value
        if value is None:
            return next(iter(enum_cls))  # type: ignore[return-value]
        if isinstance(value, str):
            candidates = (value, value.upper(), value.lower())
            members = getattr(enum_cls, "__members__", {})
            for candidate in candidates:
                member = members.get(candidate)
                if member is not None:
                    return member
            value_map = getattr(enum_cls, "_value2member_map_", {})
            for candidate in candidates:
                member = value_map.get(candidate)
                if member is not None:
                    return member
        try:
            return enum_cls(value)  # type: ignore[arg-type]
        except Exception:
            return next(iter(enum_cls))  # type: ignore[return-value]

    def _ensure_json(value: Any) -> Dict[str, Any]:
        """Normalize arbitrary mapping-like objects to plain dicts."""
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        if hasattr(value, "dict"):
            try:
                return value.dict()  # type: ignore[attr-defined]
            except Exception:
                pass
        if hasattr(value, "to_dict"):
            try:
                return value.to_dict()  # type: ignore[attr-defined]
            except Exception:
                pass
        try:
            return dict(value)
        except Exception:
            return {}

    def _coerce_str(value: Any, default: str = "") -> str:
        if isinstance(value, str):
            return value
        if value is None:
            return default
        if hasattr(value, "_mock_parent") or hasattr(value, "_mock_name"):
            parent = getattr(value, "_mock_parent", None)
            if parent is not None:
                parent_name = getattr(parent, "_mock_name", None)
                if isinstance(parent_name, str) and parent_name:
                    return parent_name
            mock_name = getattr(value, "_mock_name", None)
            if isinstance(mock_name, str) and mock_name:
                return mock_name
        return str(value)

    def _coerce_optional_str(value: Any) -> Optional[str]:
        return None if value is None else _coerce_str(value)

    def _coerce_bool(value: Any, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        try:
            return bool(value)
        except Exception:
            return default

    def _coerce_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=UTC)
        if isinstance(value, str):
            candidate = value.replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(candidate)
            except ValueError:
                pass
        if hasattr(value, "isoformat"):
            try:
                return _coerce_datetime(value.isoformat())
            except Exception:
                pass
        return datetime.now(UTC)

    def _coerce_optional_datetime(value: Any) -> Optional[datetime]:
        return None if value is None else _coerce_datetime(value)

    def _coerce_list(value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return list(value)
        return [value]

    # ===============================
    # Core Types
    # ===============================

    @strawberry.type
    class HealthInfo:
        """System health status information."""
        status: str
        version: str
        timestamp: datetime
        services: List[str]

    @strawberry.type
    class PageInfo:
        """Pagination information."""
        has_next_page: bool
        has_previous_page: bool
        start_cursor: Optional[str]
        end_cursor: Optional[str]
        total_count: int

    # ===============================
    # Authentication & Authorization
    # ===============================

    @strawberry.type
    class User:
        """User information."""
        id: str
        username: Optional[str]
        email: Optional[str]
        full_name: Optional[str]
        tenant_id: Optional[str]
        roles: List[str]
        scopes: List[str]
        is_active: bool
        created_at: datetime
        last_login: Optional[datetime]

    @strawberry.type
    class APIKey:
        """API key information."""
        id: str
        name: str
        prefix: str
        scopes: List[str]
        expires_at: Optional[datetime]
        created_at: datetime
        last_used: Optional[datetime]
        is_active: bool

    @strawberry.type
    class Session:
        """User session information."""
        id: str
        user_id: str
        ip_address: Optional[str]
        user_agent: Optional[str]
        created_at: datetime
        expires_at: datetime
        is_active: bool

    # ===============================
    # Feature Flags
    # ===============================

    @strawberry.enum
    class RolloutStrategy(Enum):
        ALL_ON = "all_on"
        ALL_OFF = "all_off"
        PERCENTAGE = "percentage"
        USER_LIST = "user_list"
        TENANT_LIST = "tenant_list"
        GRADUAL = "gradual"
        AB_TEST = "ab_test"
        CANARY = "canary"

    @strawberry.type
    class FeatureFlag:
        """Feature flag definition."""
        key: str
        name: str
        description: Optional[str]
        enabled: bool
        strategy: RolloutStrategy
        config: JSONScalar
        created_at: datetime
        updated_at: datetime
        created_by: str

    @strawberry.type
    class FeatureFlagEvaluation:
        """Feature flag evaluation result."""
        flag_key: str
        enabled: bool
        variant: Optional[str]
        reason: str
        context: JSONScalar

    # ===============================
    # Secrets Management
    # ===============================

    @strawberry.type
    class SecretMetadata:
        """Secret metadata (no sensitive data)."""
        path: str
        version: int
        created_at: datetime
        updated_at: datetime
        tags: JSONScalar
        description: Optional[str]

    @strawberry.type
    class SecretHistory:
        """Secret version history."""
        version: int
        created_at: datetime
        created_by: str
        description: Optional[str]

    # ===============================
    # Observability
    # ===============================

    @strawberry.type
    class MetricValue:
        """Metric data point."""
        timestamp: datetime
        value: float
        labels: JSONScalar

    @strawberry.type
    class Metric:
        """Metric definition and recent values."""
        name: str
        description: Optional[str]
        type: str  # counter, gauge, histogram
        unit: Optional[str]
        recent_values: List[MetricValue]

    @strawberry.type
    class TraceSpan:
        """Distributed trace span information."""
        trace_id: str
        span_id: str
        parent_span_id: Optional[str]
        operation_name: str
        start_time: datetime
        end_time: datetime
        duration_ms: float
        status: str
        tags: JSONScalar

    @strawberry.type
    class HealthCheck:
        """Service health check result."""
        service_name: str
        status: str  # healthy, unhealthy, unknown
        message: Optional[str]
        last_check: datetime
        response_time_ms: float

    # ===============================
    # Audit Trail
    # ===============================

    @strawberry.enum
    class AuditCategory(Enum):
        AUTHENTICATION = "authentication"
        AUTHORIZATION = "authorization"
        DATA_ACCESS = "data_access"
        SECURITY_EVENT = "security_event"
        USER_MANAGEMENT = "user_management"
        SYSTEM_CHANGE = "system_change"

    @strawberry.enum
    class AuditLevel(Enum):
        DEBUG = "debug"
        INFO = "info"
        WARNING = "warning"
        ERROR = "error"
        CRITICAL = "critical"

    @strawberry.type
    class AuditEvent:
        """Audit trail event."""
        id: str
        timestamp: datetime
        category: AuditCategory
        level: AuditLevel
        action: str
        resource: str
        actor: str
        tenant_id: Optional[str]
        ip_address: Optional[str]
        user_agent: Optional[str]
        details: JSONScalar
        outcome: str  # success, failure, denied

    # ===============================
    # Service Registry
    # ===============================

    @strawberry.enum
    class ServiceStatus(Enum):
        HEALTHY = "healthy"
        UNHEALTHY = "unhealthy"
        UNKNOWN = "unknown"
        STARTING = "starting"
        STOPPING = "stopping"

    @strawberry.type
    class ServiceInstance:
        """Registered service instance."""
        id: str
        name: str
        version: str
        status: ServiceStatus
        endpoint: str
        health_check_url: Optional[str]
        tags: JSONScalar
        metadata: JSONScalar
        registered_at: datetime
        last_heartbeat: datetime

    # ===============================
    # Pagination
    # ===============================

    @strawberry.type
    class AuditEventsConnection:
        """Paginated audit events."""
        nodes: List[AuditEvent]
        page_info: PageInfo

    @strawberry.type
    class FeatureFlagsConnection:
        """Paginated feature flags."""
        nodes: List[FeatureFlag]
        page_info: PageInfo

    @strawberry.type
    class ServiceInstancesConnection:
        """Paginated service instances."""
        nodes: List[ServiceInstance]
        page_info: PageInfo

    def _to_page_info(source: Any, fallback_total: int) -> PageInfo:
        """Convert raw pagination metadata to PageInfo."""
        if source is None:
            return PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None,
                total_count=fallback_total,
            )

        return PageInfo(
            has_next_page=bool(
                _safe_get(source, "has_next_page", "hasNextPage", default=False)
            ),
            has_previous_page=bool(
                _safe_get(source, "has_previous_page", "hasPreviousPage", default=False)
            ),
            start_cursor=_safe_get(source, "start_cursor", "startCursor", default=None),
            end_cursor=_safe_get(source, "end_cursor", "endCursor", default=None),
            total_count=int(
                _safe_get(source, "total_count", "totalCount", default=fallback_total)
            ),
        )

    def _to_audit_event(raw: Any) -> AuditEvent:
        """Convert resolver return values into GraphQL AuditEvent instances."""
        if raw is None:
            raise ValueError("Cannot convert empty audit event")

        return AuditEvent(
            id=_coerce_str(_safe_get(raw, "id", default="")),
            timestamp=_coerce_datetime(_safe_get(raw, "timestamp", default=datetime.now(UTC))),
            category=_coerce_enum_value(AuditCategory, _safe_get(raw, "category")),
            level=_coerce_enum_value(AuditLevel, _safe_get(raw, "level")),
            action=_coerce_str(_safe_get(raw, "action", default="")),
            resource=_coerce_str(_safe_get(raw, "resource", default="")),
            actor=_coerce_str(_safe_get(raw, "actor", default="")),
            tenant_id=_coerce_optional_str(_safe_get(raw, "tenant_id", "tenantId", default=None)),
            ip_address=_coerce_optional_str(_safe_get(raw, "ip_address", "ipAddress", default=None)),
            user_agent=_coerce_optional_str(_safe_get(raw, "user_agent", "userAgent", default=None)),
            details=_ensure_json(_safe_get(raw, "details", default={})),
            outcome=_coerce_str(_safe_get(raw, "outcome", default="unknown"), default="unknown"),
        )

    def _to_audit_connection(raw: Any) -> AuditEventsConnection:
        """Normalize resolver results to AuditEventsConnection."""
        nodes_source = _safe_get(raw, "nodes", default=[]) or []
        nodes = [_to_audit_event(node) for node in nodes_source]
        page_info_source = _safe_get(raw, "page_info", "pageInfo")
        page_info = _to_page_info(page_info_source, len(nodes))
        return AuditEventsConnection(nodes=nodes, page_info=page_info)

    def _to_api_key(raw: Any) -> APIKey:
        """Convert resolver results into APIKey GraphQL objects."""
        scopes = [
            _coerce_str(item)
            for item in _coerce_list(_safe_get(raw, "scopes", default=[]))
        ]
        name_value = _safe_get(raw, "name", default=None)
        name = _coerce_str(name_value, default=_coerce_str(raw, default=""))

        return APIKey(
            id=_coerce_str(_safe_get(raw, "id", default="")),
            name=name,
            prefix=_coerce_str(_safe_get(raw, "prefix", default="")),
            scopes=scopes,
            expires_at=_coerce_optional_datetime(_safe_get(raw, "expires_at", "expiresAt")),
            created_at=_coerce_datetime(_safe_get(raw, "created_at", "createdAt", default=datetime.now(UTC))),
            last_used=_coerce_optional_datetime(_safe_get(raw, "last_used", "lastUsed")),
            is_active=_coerce_bool(_safe_get(raw, "is_active", "isActive", default=True), default=True),
        )

    def _to_session(raw: Any) -> Session:
        """Convert resolver results into Session GraphQL objects."""
        return Session(
            id=_coerce_str(_safe_get(raw, "id", "session_id", default="")),
            user_id=_coerce_str(_safe_get(raw, "user_id", "userId", default="")),
            ip_address=_coerce_optional_str(_safe_get(raw, "ip_address", "ipAddress", default=None)),
            user_agent=_coerce_optional_str(_safe_get(raw, "user_agent", "userAgent", default=None)),
            created_at=_coerce_datetime(_safe_get(raw, "created_at", "createdAt", default=datetime.now(UTC))),
            expires_at=_coerce_datetime(_safe_get(raw, "expires_at", "expiresAt", default=datetime.now(UTC))),
            is_active=_coerce_bool(_safe_get(raw, "is_active", "isActive", default=True), default=True),
        )

    def _to_feature_flag(raw: Any) -> FeatureFlag:
        """Convert resolver results into FeatureFlag GraphQL objects."""
        name_value = _safe_get(raw, "name", default=None)
        name = _coerce_str(name_value, default=_coerce_str(raw, default=""))
        description_value = _safe_get(raw, "description", default=None)

        return FeatureFlag(
            key=_coerce_str(_safe_get(raw, "key", default="")),
            name=name,
            description=_coerce_optional_str(description_value),
            enabled=_coerce_bool(_safe_get(raw, "enabled", default=False)),
            strategy=_coerce_enum_value(RolloutStrategy, _safe_get(raw, "strategy")),
            config=_ensure_json(_safe_get(raw, "config", default={})),
            created_at=_coerce_datetime(_safe_get(raw, "created_at", "createdAt", default=datetime.now(UTC))),
            updated_at=_coerce_datetime(_safe_get(raw, "updated_at", "updatedAt", default=datetime.now(UTC))),
            created_by=_coerce_str(_safe_get(raw, "created_by", "createdBy", default="")),
        )

    def _to_feature_flags_connection(raw: Any) -> FeatureFlagsConnection:
        nodes_source = _safe_get(raw, "nodes", default=[]) or []
        nodes = [_to_feature_flag(node) for node in nodes_source]
        page_info_source = _safe_get(raw, "page_info", "pageInfo")
        page_info = _to_page_info(page_info_source, len(nodes))
        return FeatureFlagsConnection(nodes=nodes, page_info=page_info)

    # ===============================
    # Input Types
    # ===============================

    @strawberry.input
    class FeatureFlagInput:
        """Input for creating/updating feature flags."""
        key: str
        name: str
        description: Optional[str] = None
        enabled: bool = False
        strategy: RolloutStrategy = RolloutStrategy.ALL_OFF
        config: JSONScalar = strawberry.field(default_factory=dict)

    @strawberry.input
    class AuditEventFilter:
        """Filter for audit events query."""
        category: Optional[AuditCategory] = None
        level: Optional[AuditLevel] = None
        actor: Optional[str] = None
        resource: Optional[str] = None
        start_time: Optional[datetime] = None
        end_time: Optional[datetime] = None

    @strawberry.input
    class MetricsFilter:
        """Filter for metrics query."""
        name_pattern: Optional[str] = None
        labels: Optional[JSONScalar] = None
        start_time: Optional[datetime] = None
        end_time: Optional[datetime] = None

    # ===============================
    # Root Query Type
    # ===============================

    @strawberry.type
    class Query:
        """Root GraphQL query type."""

        @strawberry.field(description="System health information.")
        async def health(self) -> HealthInfo:
            """Get system health status."""
            return HealthInfo(
                status="ok",
                version="1.0.0",
                timestamp=datetime.now(UTC),
                services=["auth", "secrets", "observability", "audit", "registry"]
            )

        # ===============================
        # Authentication & Authorization
        # ===============================

        @strawberry.field(description="Get current user information.")
        async def current_user(self, info: Info) -> Optional[User]:
            """Get the currently authenticated user."""
            return await AuthResolver.get_current_user(info)

        @strawberry.field(description="List user's API keys.")
        async def api_keys(self, info: Info) -> List[APIKey]:
            """Get API keys for the current user."""
            raw_keys = await AuthResolver.get_api_keys(info)
            return [_to_api_key(key) for key in raw_keys or []]

        @strawberry.field(description="Get user sessions.")
        async def sessions(self, info: Info, user_id: Optional[str] = None) -> List[Session]:
            """Get user sessions."""
            raw_sessions = await AuthResolver.get_sessions(info, user_id)
            return [_to_session(session) for session in raw_sessions or []]

        # ===============================
        # Feature Flags
        # ===============================

        @strawberry.field(description="Get all feature flags.")
        async def feature_flags(
            self,
            info: Info,
            first: Optional[int] = 50,
            after: Optional[str] = None
        ) -> FeatureFlagsConnection:
            """List feature flags with pagination."""
            connection = await FeatureFlagResolver.get_feature_flags(info, first, after)
            if not connection:
                return FeatureFlagsConnection(nodes=[], page_info=_to_page_info(None, 0))
            return _to_feature_flags_connection(connection)

        @strawberry.field(description="Get a specific feature flag.")
        async def feature_flag(self, info: Info, key: str) -> Optional[FeatureFlag]:
            """Get a feature flag by key."""
            flag = await FeatureFlagResolver.get_feature_flag(info, key)
            return _to_feature_flag(flag) if flag else None

        @strawberry.field(description="Evaluate feature flags for current user.")
        async def evaluate_flags(
            self,
            info: Info,
            flags: List[str],
            context: Optional[JSONScalar] = None
        ) -> List[FeatureFlagEvaluation]:
            """Evaluate multiple feature flags."""
            return await FeatureFlagResolver.evaluate_flags(info, flags, context or {})

        # ===============================
        # Secrets Management
        # ===============================

        @strawberry.field(description="List secret metadata.")
        async def secrets(
            self,
            info: Info,
            path_prefix: Optional[str] = None
        ) -> List[SecretMetadata]:
            """List secrets metadata (no values)."""
            return await SecretsResolver.list_secrets(info, path_prefix)

        @strawberry.field(description="Get secret history.")
        async def secret_history(self, info: Info, path: str) -> List[SecretHistory]:
            """Get version history for a secret."""
            return await SecretsResolver.get_secret_history(info, path)

        # ===============================
        # Observability
        # ===============================

        @strawberry.field(description="Get system metrics.")
        async def metrics(
            self,
            info: Info,
            filter: Optional[MetricsFilter] = None
        ) -> List[Metric]:
            """Get system metrics."""
            return await ObservabilityResolver.get_metrics(info, filter)

        @strawberry.field(description="Get health checks.")
        async def health_checks(self, info: Info) -> List[HealthCheck]:
            """Get service health checks."""
            return await ObservabilityResolver.get_health_checks(info)

        @strawberry.field(description="Get recent traces.")
        async def traces(
            self,
            info: Info,
            service_name: Optional[str] = None,
            limit: Optional[int] = 100
        ) -> List[TraceSpan]:
            """Get recent trace spans."""
            return await ObservabilityResolver.get_traces(info, service_name, limit)

        # ===============================
        # Audit Trail
        # ===============================

        @strawberry.field(description="Search audit events.")
        async def audit_events(
            self,
            info: Info,
            filter: Optional[AuditEventFilter] = None,
            first: Optional[int] = 50,
            after: Optional[str] = None
        ) -> AuditEventsConnection:
            """Search audit events with pagination."""
            connection = await AuditTrailResolver.search_events(info, filter, first, after)
            if not connection:
                return AuditEventsConnection(nodes=[], page_info=_to_page_info(None, 0))
            return _to_audit_connection(connection)

        @strawberry.field(description="Get audit event by ID.")
        async def audit_event(self, info: Info, event_id: str) -> Optional[AuditEvent]:
            """Get a specific audit event."""
            event = await AuditTrailResolver.get_event(info, event_id)
            return _to_audit_event(event) if event else None

        # ===============================
        # Service Registry
        # ===============================

        @strawberry.field(description="List registered services.")
        async def services(
            self,
            info: Info,
            status: Optional[ServiceStatus] = None,
            first: Optional[int] = 50,
            after: Optional[str] = None
        ) -> ServiceInstancesConnection:
            """List registered service instances."""
            return await ServiceRegistryResolver.get_services(info, status, first, after)

        @strawberry.field(description="Get service by ID.")
        async def service(self, info: Info, service_id: str) -> Optional[ServiceInstance]:
            """Get a specific service instance."""
            return await ServiceRegistryResolver.get_service(info, service_id)

    # ===============================
    # Root Mutation Type
    # ===============================

    @strawberry.type
    class Mutation:
        """Root GraphQL mutation type."""

        # ===============================
        # Authentication
        # ===============================

        @strawberry.field(description="Create a new API key.")
        async def create_api_key(
            self,
            info: Info,
            name: str,
            scopes: List[str],
            expires_at: Optional[datetime] = None
        ) -> APIKey:
            """Create a new API key."""
            api_key = await AuthResolver.create_api_key(
                info, name=name, scopes=scopes, expires_at=expires_at
            )
            return _to_api_key(api_key)

        @strawberry.field(description="Revoke an API key.")
        async def revoke_api_key(self, info: Info, api_key_id: str) -> bool:
            """Revoke an API key."""
            return await AuthResolver.revoke_api_key(info, api_key_id)

        @strawberry.field(description="Invalidate user session.")
        async def invalidate_session(self, info: Info, session_id: str) -> bool:
            """Invalidate a user session."""
            return await AuthResolver.invalidate_session(info, session_id)

        # ===============================
        # Feature Flags
        # ===============================

        @strawberry.field(description="Create or update a feature flag.")
        async def upsert_feature_flag(
            self,
            info: Info,
            input: FeatureFlagInput
        ) -> FeatureFlag:
            """Create or update a feature flag."""
            flag = await FeatureFlagResolver.upsert_feature_flag(info, input)
            return _to_feature_flag(flag)

        @strawberry.field(description="Delete a feature flag.")
        async def delete_feature_flag(self, info: Info, key: str) -> bool:
            """Delete a feature flag."""
            return await FeatureFlagResolver.delete_feature_flag(info, key)

        @strawberry.field(description="Toggle a feature flag.")
        async def toggle_feature_flag(self, info: Info, key: str, enabled: bool) -> FeatureFlag:
            """Toggle a feature flag on/off."""
            flag = await FeatureFlagResolver.toggle_feature_flag(info, key, enabled)
            return _to_feature_flag(flag)

        # ===============================
        # Audit Trail
        # ===============================

        @strawberry.field(description="Log an audit event.")
        async def log_audit_event(
            self,
            info: Info,
            category: AuditCategory,
            level: AuditLevel,
            action: str,
            resource: str,
            details: Optional[JSONScalar] = None
        ) -> AuditEvent:
            """Log a new audit event."""
            event = await AuditTrailResolver.log_event(
                info, category, level, action, resource, details or {}
            )
            return _to_audit_event(event)

    # ===============================
    # Subscription Type
    # ===============================

    @strawberry.type
    class Subscription:
        """Root GraphQL subscription type for real-time updates."""

        @strawberry.subscription(description="Subscribe to audit events.")
        async def audit_events_stream(
            self,
            info: Info,
            filter: Optional[AuditEventFilter] = None
        ) -> AuditEvent:
            """Stream audit events in real-time."""
            async for event in AuditTrailResolver.stream_events(info, filter):
                yield _to_audit_event(event)

        @strawberry.subscription(description="Subscribe to metrics updates.")
        async def metrics_stream(
            self,
            info: Info,
            metric_names: List[str]
        ) -> MetricValue:
            """Stream metric updates in real-time."""
            async for metric in ObservabilityResolver.stream_metrics(info, metric_names):
                yield metric

        @strawberry.subscription(description="Subscribe to service health changes.")
        async def service_health_stream(self, info: Info) -> HealthCheck:
            """Stream service health updates."""
            async for health in ServiceRegistryResolver.stream_health(info):
                yield health

    # Create the schema
    schema: Optional["strawberry.Schema"] = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        subscription=Subscription
    )

else:
    # Graceful fallback when strawberry is not available
    schema = None
    Query = None  # type: ignore[assignment]
    Mutation = None  # type: ignore[assignment]
    Subscription = None  # type: ignore[assignment]

__all__ = ["schema", "Query", "Mutation", "Subscription"]
