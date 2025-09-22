"""
Tenant isolation middleware for WebSocket connections.
"""


from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from dotmac.platform.logging import get_logger
logger = get_logger(__name__)

class TenantMiddleware:
    """Handles tenant isolation for WebSocket connections."""

    def __init__(self, config):
        self.config = config
        self.default_tenant_id = config.default_tenant_id

    async def extract_tenant_info(self, websocket) -> Optional[dict[str, Any]]:
        """Extract tenant information from WebSocket connection."""
        if not self.config.tenant_isolation_enabled:
            return None

        tenant_info = {}

        # Try to extract tenant from various sources
        tenant_id = await self._extract_from_headers(websocket)
        if not tenant_id:
            tenant_id = await self._extract_from_path(websocket)
        if not tenant_id:
            tenant_id = await self._extract_from_query(websocket)
        if not tenant_id:
            tenant_id = await self._extract_from_subdomain(websocket)

        # Use default if none found
        if not tenant_id:
            tenant_id = self.default_tenant_id

        tenant_info["tenant_id"] = tenant_id

        # Additional tenant metadata could be added here
        return tenant_info

    async def _extract_from_headers(self, websocket) -> Optional[str]:
        """Extract tenant ID from request headers."""
        if not hasattr(websocket, "request_headers"):
            return None

        # Check common header names
        header_names = [
            "X-Tenant-ID",
            "X-Tenant",
            "Tenant-ID",
            "Tenant",
        ]

        headers = {k.lower(): v for k, v in websocket.request_headers.raw}

        for header_name in header_names:
            value = headers.get(header_name.lower())
            if value:
                return value

        return None

    async def _extract_from_path(self, websocket) -> Optional[str]:
        """Extract tenant ID from URL path."""
        if not hasattr(websocket, "path"):
            return None

        try:
            path = websocket.path

            # Pattern: /ws/tenant/{tenant_id}
            if "/tenant/" in path:
                parts = path.split("/tenant/")
                if len(parts) > 1:
                    tenant_part = parts[1].split("/")[0]  # Get first segment after /tenant/
                    if tenant_part:
                        return tenant_part

            # Pattern: /ws/{tenant_id}
            parts = path.strip("/").split("/")
            if len(parts) >= 2 and parts[0] == "ws":
                potential_tenant = parts[1]
                # Basic validation - tenant IDs should be alphanumeric with dashes/underscores
                if potential_tenant.replace("-", "").replace("_", "").isalnum():
                    return potential_tenant

        except Exception as e:
            logger.debug(f"Error extracting tenant from path: {e}")

        return None

    async def _extract_from_query(self, websocket) -> Optional[str]:
        """Extract tenant ID from query parameters."""
        if not hasattr(websocket, "path"):
            return None

        try:
            parsed_url = urlparse(websocket.path)
            query_params = parse_qs(parsed_url.query)

            # Check common query parameter names
            param_names = ["tenant", "tenant_id", "tenantId"]

            for param_name in param_names:
                if param_name in query_params and query_params[param_name]:
                    return query_params[param_name][0]

        except Exception as e:
            logger.debug(f"Error extracting tenant from query: {e}")

        return None

    async def _extract_from_subdomain(self, websocket) -> Optional[str]:
        """Extract tenant ID from subdomain."""
        if not hasattr(websocket, "request_headers"):
            return None

        try:
            headers = {k.lower(): v for k, v in websocket.request_headers.raw}
            host = headers.get("host")

            if not host:
                return None

            # Remove port if present
            host = host.split(":")[0]

            # Pattern: {tenant}.example.com
            parts = host.split(".")
            if len(parts) > 2:  # Has subdomain
                subdomain = parts[0]

                # Skip common non-tenant subdomains
                if subdomain.lower() not in ["www", "api", "app", "admin"]:
                    return subdomain

        except Exception as e:
            logger.debug(f"Error extracting tenant from subdomain: {e}")

        return None

    def validate_tenant_access(self, tenant_id: str, user_info: Any) -> bool:
        """Validate if user has access to the tenant."""
        if not self.config.tenant_isolation_enabled:
            return True

        # If user has no tenant info, they can only access default tenant
        if not hasattr(user_info, "tenant_id") or not user_info.tenant_id:
            return tenant_id == self.default_tenant_id

        # User can access their own tenant
        if user_info.tenant_id == tenant_id:
            return True

        # Check if user has admin role (can access any tenant)
        if hasattr(user_info, "has_role") and user_info.has_role("admin"):
            return True

        # Check for multi-tenant permissions
        if hasattr(user_info, "has_permission"):
            if user_info.has_permission(f"tenant:{tenant_id}:access"):
                return True
            if user_info.has_permission("tenant:*:access"):
                return True

        return False

    def get_tenant_channel_prefix(self, tenant_id: str) -> str:
        """Get channel prefix for tenant isolation."""
        if not self.config.tenant_isolation_enabled or tenant_id == self.default_tenant_id:
            return ""

        return f"tenant:{tenant_id}:"

    def enforce_tenant_channel_isolation(self, channel_name: str, tenant_id: str) -> str:
        """Enforce tenant isolation on channel names."""
        if not self.config.tenant_isolation_enabled:
            return channel_name

        prefix = self.get_tenant_channel_prefix(tenant_id)

        # If channel already has tenant prefix, use as-is
        if channel_name.startswith(f"tenant:{tenant_id}:"):
            return channel_name

        # If channel starts with another tenant prefix, reject it
        if channel_name.startswith("tenant:") and not channel_name.startswith(
            f"tenant:{tenant_id}:"
        ):
            raise ValueError("Cannot access channel from different tenant")

        # Add tenant prefix to regular channels
        return f"{prefix}{channel_name}"

    def get_stats(self) -> dict[str, Any]:
        """Get tenant middleware statistics."""
        return {
            "tenant_isolation_enabled": self.config.tenant_isolation_enabled,
            "default_tenant_id": self.default_tenant_id,
        }
