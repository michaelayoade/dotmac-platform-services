"""
FastAPI middleware for automatic audit logging.
"""

import re
import time
from collections.abc import Callable
from typing import Any, Optional, Set

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .logger import AuditLogger, get_audit_logger
from .models import AuditActor, AuditContext, AuditEventType, AuditOutcome, AuditResource, AuditSeverity

logger = structlog.get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically audit HTTP requests."""

    def __init__(
        self,
        app,
        audit_logger: AuditLogger = None,
        include_paths: Optional[list] = None,
        exclude_paths: Optional[list] = None,
        audit_all_requests: bool = False,
        enable_redaction: bool = True,
    ):
        super().__init__(app)
        self.audit_logger = audit_logger or get_audit_logger()
        self.include_paths = include_paths or []
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
        self.audit_all_requests = audit_all_requests
        self.enable_redaction = enable_redaction

        # Initialize redaction settings
        self.sensitive_keys = {
            "password", "passwd", "pwd", "secret", "token", "key", "auth", 
            "authorization", "bearer", "cookie", "session", "api_key",
            "access_token", "refresh_token", "jwt", "signature", "hash",
            "private_key", "public_key", "x-api-key", "x-auth-token",
            "credit_card", "ccn", "ssn", "social_security", "bank_account"
        }

        self.sensitive_patterns = [
            (r'\b[A-Za-z0-9]{20,}\b', 'TOKEN_REDACTED'),
            (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 'CARD_REDACTED'),
            (r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', 'Bearer TOKEN_REDACTED'),
            (r'Basic\s+[A-Za-z0-9+/]+=*', 'Basic AUTH_REDACTED'),
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and audit if needed."""

        start_time = time.time()

        # Check if path should be audited
        path = request.url.path
        should_audit = self._should_audit_path(path)

        if not should_audit:
            return await call_next(request)

        # Extract user info
        user = getattr(request.state, "user", None)
        user_id = getattr(user, "id", None) if user else None
        tenant_id = getattr(user, "tenant_id", None) if user else None

        # Create audit context
        context = AuditContext(
            request_id=getattr(request.state, "request_id", None),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            service_name="dotmac-security",
        )

        # Create actor
        actor = None
        if user_id:
            actor = AuditActor(
                actor_id=str(user_id),
                actor_type="user",
                tenant_id=tenant_id,
            )

        # Create resource
        resource = AuditResource(
            resource_type="api",
            resource_id=path,
            resource_name=f"{request.method} {path}",
        )

        # Process request
        response = None
        outcome = AuditOutcome.SUCCESS
        error_message = None

        try:
            response = await call_next(request)

            # Determine outcome based on status code
            if response.status_code >= 400:
                outcome = AuditOutcome.FAILURE

        except Exception as e:
            outcome = AuditOutcome.FAILURE
            error_message = str(e)
            logger.error("Request processing failed", path=path, error=str(e))
            raise

        finally:
            # Log audit event if logger is available
            if self.audit_logger:
                duration_ms = (time.time() - start_time) * 1000

                # Determine event type and severity
                event_type = self._get_event_type(request.method)
                severity = self._get_severity(outcome, response.status_code if response else 500)

                message = f"{request.method} {path}"
                if error_message:
                    message += f" - {error_message}"
                elif response:
                    message += f" - {response.status_code}"

                try:
                    await self.audit_logger.log_event(
                        event_type=event_type,
                        message=message,
                        actor=actor,
                        resource=resource,
                        context=context,
                        severity=severity,
                        outcome=outcome,
                        duration_ms=duration_ms,
                        custom_attributes=self._prepare_audit_attributes(request, response),
                    )
                except Exception as e:
                    logger.error("Failed to log audit event", error=str(e))

        return response

    def _should_audit_path(self, path: str) -> bool:
        """Determine if path should be audited."""

        # Check exclude list first
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return False

        # If audit_all_requests is True, audit everything not excluded
        if self.audit_all_requests:
            return True

        # Check include list
        for include_path in self.include_paths:
            if path.startswith(include_path):
                return True

        return False

    def _get_event_type(self, method: str) -> AuditEventType:
        """Map HTTP method to audit event type."""
        method_map = {
            "GET": AuditEventType.DATA_READ,
            "POST": AuditEventType.DATA_CREATE,
            "PUT": AuditEventType.DATA_UPDATE,
            "PATCH": AuditEventType.DATA_UPDATE,
            "DELETE": AuditEventType.DATA_DELETE,
        }
        return method_map.get(method.upper(), AuditEventType.DATA_READ)

    def _get_severity(self, outcome: AuditOutcome, status_code: int) -> AuditSeverity:
        """Determine audit severity based on outcome and status code."""

        if outcome == AuditOutcome.FAILURE:
            if status_code >= 500:
                return AuditSeverity.HIGH
            elif status_code == 403:
                return AuditSeverity.HIGH  # Security-related
            elif status_code >= 400:
                return AuditSeverity.MEDIUM

        return AuditSeverity.LOW

    def _prepare_audit_attributes(self, request: Request, response: Optional[Response]) -> dict[str, Any]:
        """Prepare audit attributes with redaction if enabled."""
        attributes = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code if response else None,
        }

        if self.enable_redaction:
            # Redact sensitive query parameters
            query_params = dict(request.query_params)
            attributes["query_params"] = self._redact_sensitive_data(query_params)

            # Redact sensitive headers (only include safe ones)
            safe_headers = {}
            for key, value in request.headers.items():
                key_lower = key.lower()
                if not any(sensitive in key_lower for sensitive in self.sensitive_keys):
                    if key_lower in {"user-agent", "accept", "content-type", "content-length"}:
                        safe_headers[key] = value
                    else:
                        safe_headers[key] = "[FILTERED]"
                else:
                    safe_headers[key] = "[REDACTED]"

            attributes["headers"] = safe_headers
        else:
            attributes["query_params"] = dict(request.query_params)
            attributes["headers"] = dict(request.headers)

        return attributes

    def _redact_sensitive_data(self, data: Any, max_depth: int = 3) -> Any:
        """Recursively redact sensitive data from nested structures."""
        if max_depth <= 0:
            return "[MAX_DEPTH_REACHED]"

        try:
            if isinstance(data, dict):
                return self._redact_dict(data, max_depth - 1)
            elif isinstance(data, list):
                return [self._redact_sensitive_data(item, max_depth - 1) for item in data]
            elif isinstance(data, str):
                return self._redact_string(data)
            else:
                return data
        except Exception:
            return "[REDACTION_ERROR]"

    def _redact_dict(self, data: dict, max_depth: int) -> dict:
        """Redact sensitive keys in dictionary."""
        redacted = {}

        for key, value in data.items():
            key_lower = str(key).lower()

            # Check if key is sensitive
            if any(sensitive_key in key_lower for sensitive_key in self.sensitive_keys):
                redacted[key] = "[REDACTED]"
            else:
                # Recursively process value
                redacted[key] = self._redact_sensitive_data(value, max_depth)

        return redacted

    def _redact_string(self, data: str) -> str:
        """Redact sensitive patterns in string."""
        redacted = data

        # Apply regex patterns
        for pattern, replacement in self.sensitive_patterns:
            redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)

        return redacted
