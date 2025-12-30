"""
AWX Service for Ansible automation.

Provides high-level service for tenant provisioning automation via AWX.
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any

import structlog

from dotmac.platform.ansible.client import AWXClient, AWXClientError

logger = structlog.get_logger(__name__)


class ProvisioningOperation(str, Enum):
    """Types of provisioning operations."""

    PROVISION = "provision"
    DEPROVISION = "deprovision"
    UPGRADE = "upgrade"
    SCALE = "scale"
    RESTART = "restart"


@dataclass
class ProvisioningResult:
    """Result of a provisioning operation."""

    success: bool
    status: str
    job_id: int | None = None
    job_status: str | None = None
    message: str | None = None
    outputs: dict[str, Any] | None = None


class AWXService:
    """AWX service for tenant automation."""

    # Default template naming convention
    TEMPLATE_PROVISION_SUFFIX = "-provision"
    TEMPLATE_DEPROVISION_SUFFIX = "-deprovision"
    TEMPLATE_UPGRADE_SUFFIX = "-upgrade"

    # Job polling configuration
    DEFAULT_POLL_INTERVAL = 10  # seconds
    DEFAULT_TIMEOUT = 3600  # 1 hour

    def __init__(
        self,
        client: AWXClient | None = None,
        default_template_prefix: str = "tenant",
    ) -> None:
        """
        Initialize AWX service.

        Args:
            client: AWX client instance
            default_template_prefix: Prefix for template names (e.g., "tenant" -> "tenant-provision")
        """
        self.client = client or AWXClient()
        self.default_template_prefix = default_template_prefix

    @dataclass(frozen=True)
    class JobLaunchResult:
        status: str
        job_id: int | None = None
        reason: str | None = None

    @dataclass(frozen=True)
    class JobStatus:
        status: str
        job_id: int | None = None
        reason: str | None = None
        is_terminal: bool = False
        failed: bool = False

    @property
    def is_available(self) -> bool:
        """Check if AWX service is available."""
        return self.client.is_configured

    async def provision_tenant(
        self,
        tenant_id: str,
        tenant_config: dict[str, Any],
        template_id: int | None = None,
        wait_for_completion: bool = False,
        timeout: int | None = None,
    ) -> ProvisioningResult:
        """
        Provision a new tenant using AWX.

        Args:
            tenant_id: ID of the tenant to provision
            tenant_config: Tenant configuration including:
                - name: Tenant name
                - slug: Tenant slug/subdomain
                - plan_type: Subscription plan
                - region: Target region
                - resources: Resource requirements (cpu, memory, storage)
                - features: Enabled features
                - custom_config: Any custom configuration
            template_id: Specific AWX template ID to use (optional)
            wait_for_completion: Whether to wait for job completion
            timeout: Timeout in seconds when waiting

        Returns:
            ProvisioningResult with job details
        """
        if not self.is_available:
            logger.warning("AWX service not available, skipping provisioning")
            return ProvisioningResult(
                success=False,
                status="skipped",
                message="AWX not configured",
            )

        logger.info(
            "Provisioning tenant via AWX",
            tenant_id=tenant_id,
            template_id=template_id,
        )

        # Build extra_vars for Ansible playbook
        extra_vars = self._build_provision_vars(tenant_id, tenant_config)

        # Use provided template_id or search by convention
        if template_id is None:
            # Try to find template by naming convention
            template_name = f"{self.default_template_prefix}{self.TEMPLATE_PROVISION_SUFFIX}"
            template = await self._find_template_by_name(template_name)
            if template:
                template_id = template["id"]
            else:
                return ProvisioningResult(
                    success=False,
                    status="error",
                    message=f"Provisioning template not found: {template_name}",
                )

        try:
            # Launch the provisioning job
            result = await self.client.launch_job_template(
                template_id=template_id,
                extra_vars=extra_vars,
            )

            job_id = result.get("job_id")

            if not job_id:
                return ProvisioningResult(
                    success=False,
                    status="error",
                    message="Failed to launch job - no job ID returned",
                )

            logger.info(
                "Tenant provisioning job launched",
                tenant_id=tenant_id,
                job_id=job_id,
            )

            # Optionally wait for completion
            if wait_for_completion:
                final_status = await self._wait_for_job(
                    job_id,
                    timeout=timeout or self.DEFAULT_TIMEOUT,
                )

                return ProvisioningResult(
                    success=final_status.get("status") == "successful",
                    status=final_status.get("status", "unknown"),
                    job_id=job_id,
                    job_status=final_status.get("status"),
                    message=final_status.get("job_explanation"),
                )

            return ProvisioningResult(
                success=True,
                status="launched",
                job_id=job_id,
                job_status="pending",
            )

        except AWXClientError as e:
            logger.error(
                "Failed to provision tenant",
                tenant_id=tenant_id,
                error=str(e),
            )
            return ProvisioningResult(
                success=False,
                status="error",
                message=str(e),
            )

    async def deprovision_tenant(
        self,
        tenant_id: str,
        template_id: int | None = None,
        cleanup_data: bool = True,
        wait_for_completion: bool = False,
        timeout: int | None = None,
    ) -> ProvisioningResult:
        """
        Deprovision a tenant using AWX.

        Args:
            tenant_id: ID of the tenant to deprovision
            template_id: Specific AWX template ID to use (optional)
            cleanup_data: Whether to cleanup tenant data
            wait_for_completion: Whether to wait for job completion
            timeout: Timeout in seconds when waiting

        Returns:
            ProvisioningResult with job details
        """
        if not self.is_available:
            return ProvisioningResult(
                success=False,
                status="skipped",
                message="AWX not configured",
            )

        logger.info(
            "Deprovisioning tenant via AWX",
            tenant_id=tenant_id,
            cleanup_data=cleanup_data,
        )

        # Build extra_vars for deprovision playbook
        extra_vars = {
            "tenant_id": tenant_id,
            "operation": "deprovision",
            "cleanup_data": cleanup_data,
            "cleanup_resources": True,
        }

        # Use provided template_id or search by convention
        if template_id is None:
            template_name = f"{self.default_template_prefix}{self.TEMPLATE_DEPROVISION_SUFFIX}"
            template = await self._find_template_by_name(template_name)
            if template:
                template_id = template["id"]
            else:
                return ProvisioningResult(
                    success=False,
                    status="error",
                    message=f"Deprovision template not found: {template_name}",
                )

        try:
            result = await self.client.launch_job_template(
                template_id=template_id,
                extra_vars=extra_vars,
            )

            job_id = result.get("job_id")

            if not job_id:
                return ProvisioningResult(
                    success=False,
                    status="error",
                    message="Failed to launch deprovision job",
                )

            logger.info(
                "Tenant deprovision job launched",
                tenant_id=tenant_id,
                job_id=job_id,
            )

            if wait_for_completion:
                final_status = await self._wait_for_job(
                    job_id,
                    timeout=timeout or self.DEFAULT_TIMEOUT,
                )

                return ProvisioningResult(
                    success=final_status.get("status") == "successful",
                    status=final_status.get("status", "unknown"),
                    job_id=job_id,
                    job_status=final_status.get("status"),
                )

            return ProvisioningResult(
                success=True,
                status="launched",
                job_id=job_id,
                job_status="pending",
            )

        except AWXClientError as e:
            logger.error(
                "Failed to deprovision tenant",
                tenant_id=tenant_id,
                error=str(e),
            )
            return ProvisioningResult(
                success=False,
                status="error",
                message=str(e),
            )

    async def launch_job(
        self,
        template_id: int,
        extra_vars: dict[str, Any] | None = None,
    ) -> "AWXService.JobLaunchResult":
        """
        Launch a generic AWX job template.

        Args:
            template_id: AWX template ID
            extra_vars: Variables to pass to the job

        Returns:
            JobLaunchResult with status and job_id
        """
        result = await self.client.launch_job_template(template_id, extra_vars)
        status = str(result.get("status", "unknown"))
        job_id = result.get("job_id")
        reason = result.get("reason")
        return self.JobLaunchResult(status=status, job_id=job_id, reason=reason)

    async def get_job(self, job_id: int) -> "AWXService.JobStatus":
        """
        Get AWX job status by ID.

        Args:
            job_id: AWX job ID

        Returns:
            JobStatus with current status
        """
        if not self.is_available:
            return self.JobStatus(
                status="unknown",
                job_id=job_id,
                reason="AWX not configured",
            )

        result = await self.client.get_job_status(job_id)
        return self.JobStatus(
            status=str(result.get("status", "unknown")),
            job_id=job_id,
            reason=result.get("reason"),
            is_terminal=result.get("is_terminal", False),
            failed=result.get("failed", False),
        )

    async def get_job_logs(self, job_id: int) -> str:
        """
        Get job output logs.

        Args:
            job_id: AWX job ID

        Returns:
            Job stdout as string
        """
        if not self.is_available:
            return ""
        return await self.client.get_job_stdout(job_id)

    async def cancel_job(self, job_id: int) -> bool:
        """
        Cancel a running job.

        Args:
            job_id: AWX job ID

        Returns:
            True if cancelled successfully
        """
        if not self.is_available:
            return False

        result = await self.client.cancel_job(job_id)
        return result.get("status") == "canceled"

    async def health_check(self) -> dict[str, Any]:
        """Check AWX service health."""
        if not self.is_available:
            return {
                "status": "unavailable",
                "reason": "AWX not configured",
            }

        healthy = await self.client.health_check()
        return {
            "status": "healthy" if healthy else "unhealthy",
        }

    async def list_templates(
        self,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List available job templates.

        Args:
            search: Optional search query

        Returns:
            List of template info
        """
        if not self.is_available:
            return []

        result = await self.client.list_job_templates(search=search)
        return result.get("results", [])

    def _build_provision_vars(
        self,
        tenant_id: str,
        tenant_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Build extra_vars for provisioning playbook."""
        return {
            "tenant_id": tenant_id,
            "operation": "provision",
            # Tenant identity
            "tenant_name": tenant_config.get("name", ""),
            "tenant_slug": tenant_config.get("slug", ""),
            "tenant_domain": tenant_config.get("domain"),
            # Subscription/plan info
            "plan_type": tenant_config.get("plan_type", "starter"),
            "billing_cycle": tenant_config.get("billing_cycle", "monthly"),
            # Infrastructure config
            "region": tenant_config.get("region", "us-east-1"),
            "environment": tenant_config.get("environment", "production"),
            # Resource allocation
            "resources": tenant_config.get("resources", {
                "cpu": "1",
                "memory": "1Gi",
                "storage": "10Gi",
            }),
            # Feature flags
            "features": tenant_config.get("features", {}),
            # Custom configuration
            "custom_config": tenant_config.get("custom_config", {}),
            # Provisioning options
            "create_database": tenant_config.get("create_database", True),
            "setup_monitoring": tenant_config.get("setup_monitoring", True),
            "enable_backup": tenant_config.get("enable_backup", True),
        }

    async def _find_template_by_name(
        self,
        name: str,
    ) -> dict[str, Any] | None:
        """Find a job template by name."""
        if not self.is_available:
            return None

        result = await self.client.list_job_templates(search=name)
        templates = result.get("results", [])

        # Look for exact match
        for template in templates:
            if template.get("name") == name:
                return template

        # Return first partial match if no exact match
        return templates[0] if templates else None

    async def _wait_for_job(
        self,
        job_id: int,
        timeout: int = DEFAULT_TIMEOUT,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ) -> dict[str, Any]:
        """
        Wait for a job to complete.

        Args:
            job_id: AWX job ID
            timeout: Maximum wait time in seconds
            poll_interval: Time between status checks

        Returns:
            Final job status
        """
        elapsed = 0

        while elapsed < timeout:
            status = await self.client.get_job_status(job_id)

            if status.get("is_terminal"):
                logger.info(
                    "AWX job completed",
                    job_id=job_id,
                    status=status.get("status"),
                    elapsed=elapsed,
                )
                return status

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            logger.debug(
                "Waiting for AWX job",
                job_id=job_id,
                status=status.get("status"),
                elapsed=elapsed,
            )

        # Timeout reached
        logger.warning(
            "AWX job timed out",
            job_id=job_id,
            timeout=timeout,
        )

        return {
            "job_id": job_id,
            "status": "timeout",
            "is_terminal": True,
        }
