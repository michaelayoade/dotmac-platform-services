"""
Device health checking system.
"""

import asyncio
import logging
import socket
import time

from .types import (
    CheckType,
    HealthCheck,
    HealthCheckError,
    HealthCheckResult,
    HealthStatus,
)

logger = logging.getLogger(__name__)


class DeviceHealthChecker:
    """
    Device health checking engine.

    Executes various types of health checks against network devices.
    """

    def __init__(self):
        self._running = False
        self._check_handlers = {
            CheckType.PING: self._ping_check,
            CheckType.PORT: self._port_check,
            CheckType.SERVICE: self._service_check,
            CheckType.RESOURCE: self._resource_check,
            CheckType.CUSTOM: self._custom_check,
        }

    async def start(self):
        """Start health checker."""
        self._running = True
        logger.info("Device health checker started")

    async def stop(self):
        """Stop health checker."""
        self._running = False
        logger.info("Device health checker stopped")

    async def execute_check(self, check: HealthCheck) -> HealthCheckResult:
        """
        Execute health check.

        Args:
            check: Health check specification

        Returns:
            HealthCheckResult with check outcome
        """
        if not check.enabled:
            return HealthCheckResult(
                check_name=check.name,
                target=check.target,
                status=HealthStatus.UNKNOWN,
                message="Check is disabled",
            )

        start_time = time.time()

        try:
            handler = self._check_handlers.get(check.check_type)
            if not handler:
                raise HealthCheckError(
                    check.name,
                    check.target,
                    f"Unsupported check type: {check.check_type}",
                )

            result = await handler(check)
            result.execution_time = time.time() - start_time

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Health check {check.name} failed: {e}")

            return HealthCheckResult(
                check_name=check.name,
                target=check.target,
                status=HealthStatus.CRITICAL,
                message=f"Check execution failed: {str(e)}",
                execution_time=execution_time,
                error_details=str(e),
            )

    async def _ping_check(self, check: HealthCheck) -> HealthCheckResult:
        """Execute ping health check."""
        try:
            # Use subprocess to ping
            process = await asyncio.create_subprocess_exec(
                "ping",
                "-c",
                "3",
                "-W",
                str(check.timeout),
                check.target,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=check.timeout + 5
            )

            if process.returncode == 0:
                # Parse ping output for metrics
                output = stdout.decode("utf-8")
                metrics = self._parse_ping_output(output)

                return HealthCheckResult(
                    check_name=check.name,
                    target=check.target,
                    status=HealthStatus.HEALTHY,
                    message=f"Ping successful - {metrics.get('avg_time', 'N/A')}ms avg",
                    metrics=metrics,
                )
            else:
                error_msg = stderr.decode("utf-8") if stderr else "Ping failed"
                return HealthCheckResult(
                    check_name=check.name,
                    target=check.target,
                    status=HealthStatus.CRITICAL,
                    message=f"Ping failed: {error_msg}",
                    error_details=error_msg,
                )

        except asyncio.TimeoutError:
            return HealthCheckResult(
                check_name=check.name,
                target=check.target,
                status=HealthStatus.CRITICAL,
                message=f"Ping timeout after {check.timeout}s",
            )
        except Exception as e:
            return HealthCheckResult(
                check_name=check.name,
                target=check.target,
                status=HealthStatus.CRITICAL,
                message=f"Ping check error: {str(e)}",
                error_details=str(e),
            )

    async def _port_check(self, check: HealthCheck) -> HealthCheckResult:
        """Execute TCP port health check."""
        try:
            port = check.parameters.get("port", 22)

            # Create socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(check.timeout)

            try:
                result = sock.connect_ex((check.target, port))
                sock.close()

                if result == 0:
                    return HealthCheckResult(
                        check_name=check.name,
                        target=check.target,
                        status=HealthStatus.HEALTHY,
                        message=f"Port {port} is open",
                        metrics={"port": port, "status": "open"},
                    )
                else:
                    return HealthCheckResult(
                        check_name=check.name,
                        target=check.target,
                        status=HealthStatus.CRITICAL,
                        message=f"Port {port} is closed or filtered",
                        metrics={"port": port, "status": "closed"},
                    )
            finally:
                sock.close()

        except Exception as e:
            return HealthCheckResult(
                check_name=check.name,
                target=check.target,
                status=HealthStatus.CRITICAL,
                message=f"Port check error: {str(e)}",
                error_details=str(e),
            )

    async def _service_check(self, check: HealthCheck) -> HealthCheckResult:
        """Execute service health check."""
        # This would implement service-specific checks
        # For now, return a placeholder
        return HealthCheckResult(
            check_name=check.name,
            target=check.target,
            status=HealthStatus.HEALTHY,
            message="Service check not yet implemented",
        )

    async def _resource_check(self, check: HealthCheck) -> HealthCheckResult:
        """Execute resource utilization check."""
        # This would implement resource monitoring
        # For now, return a placeholder
        return HealthCheckResult(
            check_name=check.name,
            target=check.target,
            status=HealthStatus.HEALTHY,
            message="Resource check not yet implemented",
        )

    async def _custom_check(self, check: HealthCheck) -> HealthCheckResult:
        """Execute custom health check."""
        if not check.custom_check:
            return HealthCheckResult(
                check_name=check.name,
                target=check.target,
                status=HealthStatus.CRITICAL,
                message="Custom check function not provided",
            )

        try:
            if asyncio.iscoroutinefunction(check.custom_check):
                result = await check.custom_check(check)
            else:
                result = check.custom_check(check)

            if isinstance(result, HealthCheckResult):
                return result
            else:
                # Assume boolean result
                status = HealthStatus.HEALTHY if result else HealthStatus.CRITICAL
                return HealthCheckResult(
                    check_name=check.name,
                    target=check.target,
                    status=status,
                    message=f"Custom check {'passed' if result else 'failed'}",
                )

        except Exception as e:
            return HealthCheckResult(
                check_name=check.name,
                target=check.target,
                status=HealthStatus.CRITICAL,
                message=f"Custom check error: {str(e)}",
                error_details=str(e),
            )

    def _parse_ping_output(self, output: str) -> dict[str, any]:
        """Parse ping command output for metrics."""
        metrics = {}

        try:
            lines = output.split("\n")
            for line in lines:
                if "packets transmitted" in line:
                    # Extract packet loss
                    parts = line.split()
                    transmitted = int(parts[0])
                    received = int(parts[3])
                    loss_percent = ((transmitted - received) / transmitted) * 100
                    metrics["packet_loss"] = loss_percent
                    metrics["packets_sent"] = transmitted
                    metrics["packets_received"] = received

                elif line.startswith("round-trip"):
                    # Extract timing information
                    parts = line.split("=")[1].strip().split("/")
                    if len(parts) >= 4:
                        metrics["min_time"] = float(parts[0])
                        metrics["avg_time"] = float(parts[1])
                        metrics["max_time"] = float(parts[2])
                        metrics["mdev_time"] = float(parts[3].split()[0])

        except Exception as e:
            logger.debug(f"Error parsing ping output: {e}")

        return metrics
