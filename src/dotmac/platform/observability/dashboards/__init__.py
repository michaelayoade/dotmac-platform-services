"""Dashboard provisioning and management for DotMac observability."""

from .manager import (
    DashboardConfig,
    DashboardProvisioningResult,
    provision_platform_dashboards,
)
from .provisioning import DashboardProvisioner


# Primary dashboard class for SigNoz
class SigNozDashboard:
    """SigNoz dashboard management."""

    def __init__(self, config=None) -> None:
        self.config = config or {}

    def create_dashboard(self, dashboard_spec) -> None:
        """Create SigNoz dashboard from specification."""
        # Implementation would call SigNoz API


__all__ = [
    "DashboardConfig",
    "DashboardProvisioner",
    "DashboardProvisioningResult",
    "SigNozDashboard",
    "provision_platform_dashboards",
]
