"""
Device provisioning engine using SSH automation.
"""

import asyncio
import logging
from typing import Optional
from uuid import uuid4

from .automation import SSHAutomation
from .types import (
    DeviceConfig,
    ProvisioningError,
    ProvisioningJob,
    ProvisioningStatus,
    ProvisioningTemplate,
)

logger = logging.getLogger(__name__)


class DeviceProvisioner:
    """
    Device provisioning engine.

    Manages device provisioning workflows using templates and SSH automation.
    """

    def __init__(self):
        self.ssh_automation = SSHAutomation()
        self._jobs: dict[str, ProvisioningJob] = {}
        self._templates: dict[str, ProvisioningTemplate] = {}
        self._running = False

    async def start(self):
        """Start provisioning engine."""
        self._running = True
        logger.info("Device provisioner started")

    async def stop(self):
        """Stop provisioning engine."""
        self._running = False
        await self.ssh_automation.disconnect_all()
        logger.info("Device provisioner stopped")

    def add_template(self, template: ProvisioningTemplate):
        """Add provisioning template."""
        self._templates[template.name] = template
        logger.info(f"Added provisioning template: {template.name}")

    def get_template(self, name: str) -> Optional[ProvisioningTemplate]:
        """Get provisioning template by name."""
        return self._templates.get(name)

    def list_templates(self) -> list[ProvisioningTemplate]:
        """List all provisioning templates."""
        return list(self._templates.values())

    async def provision_device(
        self,
        device_config: DeviceConfig,
        template: ProvisioningTemplate,
        variables: Optional[dict[str, any]] = None,
    ) -> ProvisioningJob:
        """
        Provision device using template.

        Args:
            device_config: Device configuration
            template: Provisioning template to use
            variables: Template variables

        Returns:
            ProvisioningJob tracking the provisioning process
        """
        job_id = str(uuid4())
        job = ProvisioningJob(
            job_id=job_id,
            device_config=device_config,
            template=template,
            variables=variables or {},
        )

        self._jobs[job_id] = job

        # Start provisioning in background
        asyncio.create_task(self._execute_provisioning_job(job))

        return job

    async def _execute_provisioning_job(self, job: ProvisioningJob):
        """Execute provisioning job."""
        try:
            job.mark_started()
            logger.info(
                f"Starting provisioning job {job.job_id} for device {job.device_config.hostname}"
            )

            # Render template with variables
            rendered_template = job.template.render_template(job.variables)

            # Connect to device
            connection = await self.ssh_automation.connect(
                host=job.device_config.ip_address,
                credentials=job.device_config.credentials,
                config=job.device_config.connection_config,
                device_type=job.device_config.device_type,
            )

            try:
                # Execute provisioning steps
                for step in rendered_template.steps:
                    job.current_step = step.name
                    logger.info(f"Executing step '{step.name}' for job {job.job_id}")

                    try:
                        # Execute step command
                        response = await self.ssh_automation.execute_command(
                            connection.connection_id, step.command
                        )

                        # Record step result
                        job.add_step_result(step.name, response)

                        # Check if step succeeded
                        if not response.success:
                            if step.required:
                                raise ProvisioningError(
                                    job.job_id,
                                    step.name,
                                    f"Required step failed: {response.error_message}",
                                )
                            else:
                                logger.warning(
                                    f"Optional step '{step.name}' failed: {response.error_message}"
                                )

                        # Check custom condition if provided
                        if step.condition and not step.condition(response):
                            if step.required:
                                raise ProvisioningError(
                                    job.job_id, step.name, "Step condition check failed"
                                )

                        logger.info(
                            f"Step '{step.name}' completed successfully for job {job.job_id}"
                        )

                    except Exception as e:
                        logger.error(
                            f"Step '{step.name}' failed for job {job.job_id}: {e}"
                        )

                        # Try rollback if available
                        if step.rollback_command:
                            try:
                                logger.info(
                                    f"Executing rollback for step '{step.name}'"
                                )
                                rollback_response = (
                                    await self.ssh_automation.execute_command(
                                        connection.connection_id, step.rollback_command
                                    )
                                )
                                if not rollback_response.success:
                                    logger.error(
                                        f"Rollback failed for step '{step.name}': {rollback_response.error_message}"
                                    )
                            except Exception as rollback_error:
                                logger.error(
                                    f"Rollback exception for step '{step.name}': {rollback_error}"
                                )

                        if step.required:
                            raise

                # All steps completed successfully
                job.mark_completed()
                logger.info(f"Provisioning job {job.job_id} completed successfully")

            finally:
                # Disconnect from device
                await self.ssh_automation.disconnect(connection.connection_id)

        except Exception as e:
            job.mark_failed(str(e))
            logger.error(f"Provisioning job {job.job_id} failed: {e}")

    def get_job(self, job_id: str) -> Optional[ProvisioningJob]:
        """Get provisioning job by ID."""
        return self._jobs.get(job_id)

    def list_jobs(self) -> list[ProvisioningJob]:
        """List all provisioning jobs."""
        return list(self._jobs.values())

    def get_active_jobs(self) -> list[ProvisioningJob]:
        """Get active provisioning jobs."""
        return [
            job
            for job in self._jobs.values()
            if job.status == ProvisioningStatus.IN_PROGRESS
        ]

    def get_job_status(self, job_id: str) -> Optional[ProvisioningStatus]:
        """Get job status."""
        job = self._jobs.get(job_id)
        return job.status if job else None

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel provisioning job."""
        job = self._jobs.get(job_id)
        if job and job.status == ProvisioningStatus.IN_PROGRESS:
            job.mark_failed("Job cancelled by user")
            logger.info(f"Cancelled provisioning job {job_id}")
            return True
        return False
