"""
Frontend Configuration Bridge

This module provides configuration helpers to generate frontend-compatible
configuration from the backend platform configuration.
"""

import json
import os
from typing import Any, Dict, Optional

from ..core.unified_config import get_config, PlatformConfig


class FrontendConfigBridge:
    """
    Bridge between backend platform configuration and frontend requirements.

    This class generates frontend-compatible configuration objects that can be
    consumed by the @dotmac/headless and other frontend packages.
    """

    def __init__(self, platform_config: Optional[PlatformConfig] = None):
        self.platform_config = platform_config or get_config()

    def get_api_client_config(self) -> Dict[str, Any]:
        """
        Generate API client configuration for @dotmac/http-client.

        Returns configuration that matches the HttpClientConfig interface
        in the frontend packages.
        """
        return {
            "baseURL": self._get_api_base_url(),
            "timeout": 30000,  # 30 seconds
            "retries": 3,
            "retryDelay": 1000,  # 1 second
            "tenantIdSource": "header",  # Matches backend tenant middleware
            "authTokenSource": "cookie",  # Matches backend session config
        }

    def get_websocket_config(self) -> Dict[str, Any]:
        """
        Generate WebSocket configuration for real-time features.

        Used by @dotmac/headless useWebSocket hooks.
        """
        return {
            "url": self._get_websocket_url(),
            "reconnectAttempts": 5,
            "reconnectInterval": 3000,
            "heartbeatInterval": 30000,
            "auth": {
                "type": "cookie",  # Use session cookies
                "tokenRefreshUrl": f"{self._get_api_base_url()}/auth/refresh",
            },
        }

    def get_service_registry_config(self) -> Dict[str, Any]:
        """
        Generate service registry configuration for frontend service monitoring.

        Used by service monitoring dashboards and health checks.
        """
        return {
            "enabled": True,
            "apiEndpoint": f"{self._get_api_base_url()}/service-registry",
            "healthCheckInterval": self.platform_config.service_registry.health_check_interval * 1000,  # Convert to ms
            "refreshInterval": 30000,  # 30 seconds
            "features": {
                "realTimeUpdates": True,
                "healthMonitoring": True,
                "serviceDiscovery": True,
            },
        }

    def get_audit_trail_config(self) -> Dict[str, Any]:
        """
        Generate audit trail configuration for compliance dashboards.

        Used by @dotmac/analytics and audit dashboard components.
        """
        return {
            "enabled": True,
            "apiEndpoint": f"{self._get_api_base_url()}/audit-trail",
            "features": {
                "realTimeAlerts": self.platform_config.audit_trail.anomaly_detection_enabled,
                "complianceReporting": self.platform_config.audit_trail.compliance_enabled,
                "dataExport": True,
                "anomalyDetection": self.platform_config.audit_trail.anomaly_detection_enabled,
            },
            "exportFormats": self.platform_config.audit_trail.export_formats,
            "alertThresholds": {
                "critical": self.platform_config.audit_trail.alert_threshold_critical,
                "warning": self.platform_config.audit_trail.alert_threshold_warning,
            },
        }

    def get_distributed_locks_config(self) -> Dict[str, Any]:
        """
        Generate distributed locks configuration for optimistic UI updates.

        Used by useOptimisticUpdate and conflict resolution hooks.
        """
        return {
            "enabled": True,
            "apiEndpoint": f"{self._get_api_base_url()}/distributed-locks",
            "defaultTimeout": self.platform_config.distributed_locks.default_timeout * 1000,  # Convert to ms
            "features": {
                "optimisticUpdates": True,
                "conflictResolution": True,
                "autoRenewal": self.platform_config.distributed_locks.auto_renewal_enabled,
            },
            "ui": {
                "showLockStatus": True,
                "conflictWarnings": True,
                "lockTimeoutWarnings": True,
            },
        }

    def get_authentication_config(self) -> Dict[str, Any]:
        """
        Generate authentication configuration for frontend auth hooks.

        Used by @dotmac/headless useAuth, useMFA, and authentication providers.
        """
        return {
            "apiEndpoint": f"{self._get_api_base_url()}/auth",
            "sessionConfig": {
                "tokenType": "jwt",
                "storage": "cookie",  # Secure HttpOnly cookies
                "refreshThreshold": 300,  # Refresh 5 minutes before expiry
                "sessionTimeout": self.platform_config.session.session_timeout * 1000,  # Convert to ms
            },
            "mfa": {
                "enabled": self.platform_config.mfa.enabled,
                "methods": ["totp"],  # TOTP support
                "required": self.platform_config.mfa.enforce_mfa,
            },
            "features": {
                "passwordReset": True,
                "accountLocking": True,
                "sessionManagement": True,
                "auditLogging": True,
            },
        }

    def get_tenant_config(self) -> Dict[str, Any]:
        """
        Generate tenant configuration for multi-tenant UI.

        Used by @dotmac/headless useISPTenant and tenant providers.
        """
        return {
            "enabled": self.platform_config.tenant.multi_tenant_enabled,
            "apiEndpoint": f"{self._get_api_base_url()}/tenant",
            "isolation": {
                "level": "namespace",  # tenant isolation level
                "enforcement": "strict",
            },
            "features": {
                "tenantSwitching": True,
                "tenantBranding": True,
                "tenantAnalytics": True,
            },
            "ui": {
                "showTenantSelector": True,
                "tenantBrandingSupport": True,
                "crossTenantWarnings": True,
            },
        }

    def get_complete_frontend_config(self) -> Dict[str, Any]:
        """
        Generate complete frontend configuration object.

        This returns a comprehensive configuration that can be used to
        initialize all frontend packages and providers.
        """
        return {
            "environment": self.platform_config.environment,
            "debug": self.platform_config.debug,
            "api": self.get_api_client_config(),
            "websocket": self.get_websocket_config(),
            "auth": self.get_authentication_config(),
            "tenant": self.get_tenant_config(),
            "services": {
                "serviceRegistry": self.get_service_registry_config(),
                "auditTrail": self.get_audit_trail_config(),
                "distributedLocks": self.get_distributed_locks_config(),
            },
            "features": {
                "serviceMonitoring": True,
                "auditDashboard": True,
                "realTimeNotifications": True,
                "optimisticUpdates": True,
                "complianceReporting": True,
            },
            "ui": {
                "theme": "auto",
                "notifications": {
                    "position": "top-right",
                    "duration": 5000,
                    "maxNotifications": 5,
                },
                "dataTable": {
                    "pageSize": 25,
                    "exportEnabled": True,
                    "filterEnabled": True,
                },
            },
        }

    def generate_env_file(self, output_path: str = "frontend/.env.local") -> None:
        """
        Generate .env file for frontend development.

        Creates environment variables that can be consumed by Vite or other
        frontend build tools.
        """
        config = self.get_complete_frontend_config()

        env_vars = {
            "VITE_API_URL": config["api"]["baseURL"],
            "VITE_WS_URL": config["websocket"]["url"],
            "VITE_ENVIRONMENT": config["environment"],
            "VITE_DEBUG": str(config["debug"]).lower(),

            # Service endpoints
            "VITE_SERVICE_REGISTRY_ENDPOINT": config["services"]["serviceRegistry"]["apiEndpoint"],
            "VITE_AUDIT_TRAIL_ENDPOINT": config["services"]["auditTrail"]["apiEndpoint"],
            "VITE_DISTRIBUTED_LOCKS_ENDPOINT": config["services"]["distributedLocks"]["apiEndpoint"],

            # Feature flags
            "VITE_FEATURE_SERVICE_MONITORING": str(config["features"]["serviceMonitoring"]).lower(),
            "VITE_FEATURE_AUDIT_DASHBOARD": str(config["features"]["auditDashboard"]).lower(),
            "VITE_FEATURE_REALTIME": str(config["features"]["realTimeNotifications"]).lower(),
            "VITE_FEATURE_OPTIMISTIC_UPDATES": str(config["features"]["optimisticUpdates"]).lower(),

            # Authentication
            "VITE_AUTH_MFA_ENABLED": str(config["auth"]["mfa"]["enabled"]).lower(),
            "VITE_AUTH_SESSION_TIMEOUT": str(config["auth"]["sessionConfig"]["sessionTimeout"]),

            # Tenant configuration
            "VITE_TENANT_ENABLED": str(config["tenant"]["enabled"]).lower(),
        }

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write environment file
        with open(output_path, "w") as f:
            f.write("# Auto-generated frontend configuration\n")
            f.write("# Generated from backend platform configuration\n\n")

            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")

        print(f"Frontend environment file generated: {output_path}")

    def generate_typescript_config(self, output_path: str = "frontend/src/config/backend-config.ts") -> None:
        """
        Generate TypeScript configuration file for frontend.

        Creates a strongly-typed configuration object that can be imported
        directly into frontend code.
        """
        config = self.get_complete_frontend_config()

        ts_content = '''// Auto-generated frontend configuration
// Generated from backend platform configuration
// Do not edit manually - regenerate using the config bridge

export interface BackendConfig {
  environment: string;
  debug: boolean;
  api: {
    baseURL: string;
    timeout: number;
    retries: number;
    retryDelay: number;
    tenantIdSource: string;
    authTokenSource: string;
  };
  websocket: {
    url: string;
    reconnectAttempts: number;
    reconnectInterval: number;
    heartbeatInterval: number;
  };
  auth: {
    apiEndpoint: string;
    sessionConfig: {
      tokenType: string;
      storage: string;
      refreshThreshold: number;
      sessionTimeout: number;
    };
    mfa: {
      enabled: boolean;
      methods: string[];
      required: boolean;
    };
  };
  services: {
    serviceRegistry: {
      enabled: boolean;
      apiEndpoint: string;
      healthCheckInterval: number;
    };
    auditTrail: {
      enabled: boolean;
      apiEndpoint: string;
      features: {
        realTimeAlerts: boolean;
        complianceReporting: boolean;
        anomalyDetection: boolean;
      };
    };
    distributedLocks: {
      enabled: boolean;
      apiEndpoint: string;
      defaultTimeout: number;
    };
  };
}

export const backendConfig: BackendConfig = ''' + json.dumps(config, indent=2) + ''';

export default backendConfig;
'''

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write TypeScript file
        with open(output_path, "w") as f:
            f.write(ts_content)

        print(f"TypeScript configuration generated: {output_path}")

    def _get_api_base_url(self) -> str:
        """Get API base URL from configuration or environment."""
        # Check for explicit API gateway configuration
        if hasattr(self.platform_config, 'api_gateway'):
            return getattr(self.platform_config.api_gateway, 'base_url', 'http://localhost:8000')

        # Fallback to environment or default
        return os.getenv("API_BASE_URL", "http://localhost:8000")

    def _get_websocket_url(self) -> str:
        """Get WebSocket URL from configuration or environment."""
        api_url = self._get_api_base_url()

        # Convert HTTP to WebSocket URL
        if api_url.startswith("https://"):
            ws_url = api_url.replace("https://", "wss://")
        else:
            ws_url = api_url.replace("http://", "ws://")

        return f"{ws_url}/ws"


# Global configuration bridge instance
_config_bridge = None


def get_frontend_config() -> Dict[str, Any]:
    """Get the complete frontend configuration."""
    global _config_bridge
    if _config_bridge is None:
        _config_bridge = FrontendConfigBridge()
    return _config_bridge.get_complete_frontend_config()


def generate_frontend_config_files(frontend_dir: str = "frontend") -> None:
    """
    Generate both .env and TypeScript configuration files for frontend.

    Args:
        frontend_dir: Path to the frontend directory
    """
    bridge = FrontendConfigBridge()

    # Generate environment file
    env_path = os.path.join(frontend_dir, ".env.local")
    bridge.generate_env_file(env_path)

    # Generate TypeScript config
    ts_path = os.path.join(frontend_dir, "src", "config", "backend-config.ts")
    bridge.generate_typescript_config(ts_path)

    print(f"Frontend configuration files generated in {frontend_dir}")


if __name__ == "__main__":
    # CLI usage: python -m dotmac.platform.frontend.config_bridge
    import sys

    if len(sys.argv) > 1:
        frontend_dir = sys.argv[1]
    else:
        frontend_dir = "frontend"

    generate_frontend_config_files(frontend_dir)