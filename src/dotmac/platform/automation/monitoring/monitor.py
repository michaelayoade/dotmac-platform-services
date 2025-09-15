"""
Network monitoring system for infrastructure health and performance tracking.
"""

import asyncio
import logging
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Optional

from .health import DeviceHealthChecker
from .snmp import SNMPCollector
from .types import (
    Alert,
    AlertRule,
    DeviceMetrics,
    HealthCheck,
    HealthCheckResult,
    HealthStatus,
    MonitoringConfig,
    MonitoringProtocol,
    MonitoringTarget,
)

logger = logging.getLogger(__name__)


class NetworkMonitor:
    """
    Comprehensive network monitoring system.

    Provides centralized monitoring for:
    - Device health and availability
    - Performance metrics collection
    - Alert management and notifications
    - Network topology discovery
    - Historical data retention
    """

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self._running = False

        # Component managers
        self.health_checker = DeviceHealthChecker()
        self.snmp_collector = SNMPCollector()

        # Storage
        self._targets: dict[str, MonitoringTarget] = {}
        self._health_checks: dict[str, HealthCheck] = {}
        self._alert_rules: dict[str, AlertRule] = {}
        self._active_alerts: dict[str, Alert] = {}

        # Metrics storage (in-memory for this implementation)
        self._metrics: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._device_metrics: dict[str, DeviceMetrics] = {}

        # Health check results
        self._health_results: dict[str, HealthCheckResult] = {}

        # Event handlers
        self._metric_handlers: list[Callable] = []
        self._alert_handlers: list[Callable] = []
        self._health_handlers: list[Callable] = []

        # Tasks
        self._monitor_tasks: list[asyncio.Task] = []

    async def start(self):
        """Start the monitoring system."""
        if self._running:
            logger.warning("Network monitor is already running")
            return

        self._running = True
        logger.info("Starting network monitoring system")

        # Start component managers
        await self.health_checker.start()
        await self.snmp_collector.start()

        # Start monitoring tasks
        if self.config.enable_health_checks:
            task = asyncio.create_task(self._health_check_loop())
            self._monitor_tasks.append(task)

        if self.config.enable_metrics:
            task = asyncio.create_task(self._metrics_collection_loop())
            self._monitor_tasks.append(task)

        if self.config.enable_alerting:
            task = asyncio.create_task(self._alerting_loop())
            self._monitor_tasks.append(task)

        # Start cleanup task
        task = asyncio.create_task(self._cleanup_loop())
        self._monitor_tasks.append(task)

        logger.info("Network monitoring system started")

    async def stop(self):
        """Stop the monitoring system."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping network monitoring system")

        # Cancel monitoring tasks
        for task in self._monitor_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self._monitor_tasks:
            await asyncio.gather(*self._monitor_tasks, return_exceptions=True)

        self._monitor_tasks.clear()

        # Stop component managers
        await self.health_checker.stop()
        await self.snmp_collector.stop()

        logger.info("Network monitoring system stopped")

    # Target Management
    def add_target(self, target: MonitoringTarget):
        """Add monitoring target."""
        self._targets[target.id] = target
        logger.info(f"Added monitoring target: {target.name} ({target.host})")

    def remove_target(self, target_id: str):
        """Remove monitoring target."""
        if target_id in self._targets:
            target = self._targets[target_id]
            del self._targets[target_id]
            logger.info(f"Removed monitoring target: {target.name}")

    def get_target(self, target_id: str) -> Optional[MonitoringTarget]:
        """Get monitoring target by ID."""
        return self._targets.get(target_id)

    def list_targets(self) -> list[MonitoringTarget]:
        """List all monitoring targets."""
        return list(self._targets.values())

    # Health Check Management
    def add_health_check(self, check: HealthCheck):
        """Add health check."""
        self._health_checks[check.name] = check
        logger.info(f"Added health check: {check.name} -> {check.target}")

    def remove_health_check(self, check_name: str):
        """Remove health check."""
        if check_name in self._health_checks:
            del self._health_checks[check_name]
            logger.info(f"Removed health check: {check_name}")

    def get_health_check(self, check_name: str) -> Optional[HealthCheck]:
        """Get health check by name."""
        return self._health_checks.get(check_name)

    def list_health_checks(self) -> list[HealthCheck]:
        """List all health checks."""
        return list(self._health_checks.values())

    # Alert Rule Management
    def add_alert_rule(self, rule: AlertRule):
        """Add alert rule."""
        self._alert_rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")

    def remove_alert_rule(self, rule_name: str):
        """Remove alert rule."""
        if rule_name in self._alert_rules:
            del self._alert_rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")

    def get_alert_rule(self, rule_name: str) -> Optional[AlertRule]:
        """Get alert rule by name."""
        return self._alert_rules.get(rule_name)

    def list_alert_rules(self) -> list[AlertRule]:
        """List all alert rules."""
        return list(self._alert_rules.values())

    # Monitoring Loops
    async def _health_check_loop(self):
        """Main health checking loop."""
        while self._running:
            try:
                # Execute health checks
                tasks = []
                for check in self._health_checks.values():
                    if check.enabled:
                        task = asyncio.create_task(self._execute_health_check(check))
                        tasks.append(task)

                # Limit concurrent checks
                semaphore = asyncio.Semaphore(self.config.max_concurrent_checks)

                async def limited_check(task, sem=semaphore):
                    async with sem:
                        return await task

                limited_tasks = [limited_check(task) for task in tasks]
                if limited_tasks:
                    await asyncio.gather(*limited_tasks, return_exceptions=True)

                # Wait for next check interval
                await asyncio.sleep(self.config.check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(10)

    async def _metrics_collection_loop(self):
        """Main metrics collection loop."""
        while self._running:
            try:
                # Collect metrics from all targets
                tasks = []
                for target in self._targets.values():
                    if target.enabled:
                        task = asyncio.create_task(self._collect_target_metrics(target))
                        tasks.append(task)

                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

                # Wait for next collection interval
                await asyncio.sleep(self.config.check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(10)

    async def _alerting_loop(self):
        """Main alerting evaluation loop."""
        while self._running:
            try:
                # Evaluate alert rules
                for rule in self._alert_rules.values():
                    if rule.enabled:
                        await self._evaluate_alert_rule(rule)

                # Check for auto-resolve
                await self._check_auto_resolve()

                # Wait for next evaluation
                await asyncio.sleep(self.config.alert_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alerting loop: {e}")
                await asyncio.sleep(10)

    async def _cleanup_loop(self):
        """Cleanup old data loop."""
        while self._running:
            try:
                await self._cleanup_old_data()
                await asyncio.sleep(3600)  # Run every hour

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(300)

    # Health Check Execution
    async def _execute_health_check(self, check: HealthCheck):
        """Execute individual health check."""
        try:
            result = await self.health_checker.execute_check(check)
            self._health_results[check.name] = result

            # Notify handlers
            for handler in self._health_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(result)
                    else:
                        handler(result)
                except Exception as e:
                    logger.error(f"Error in health check handler: {e}")

            return result

        except Exception as e:
            logger.error(f"Error executing health check {check.name}: {e}")
            error_result = HealthCheckResult(
                check_name=check.name,
                target=check.target,
                status=HealthStatus.UNKNOWN,
                message=f"Check execution failed: {e}",
                error_details=str(e),
            )
            self._health_results[check.name] = error_result
            return error_result

    # Metrics Collection
    async def _collect_target_metrics(self, target: MonitoringTarget):
        """Collect metrics from target."""
        try:
            metrics = DeviceMetrics(device_id=target.id, device_name=target.name)

            # Collect SNMP metrics if supported
            if target.has_protocol(MonitoringProtocol.SNMP):
                snmp_metrics = await self.snmp_collector.collect_metrics(target)
                if snmp_metrics:
                    # Merge SNMP metrics
                    metrics.interfaces = snmp_metrics.get("interfaces", [])
                    metrics.cpu_utilization = snmp_metrics.get("cpu_utilization")
                    metrics.memory_utilization = snmp_metrics.get("memory_utilization")

            # Store metrics
            self._device_metrics[target.id] = metrics

            # Add to time series
            metric_key = f"{target.id}.metrics"
            self._metrics[metric_key].append(
                {"timestamp": metrics.timestamp, "data": metrics}
            )

            # Notify handlers
            for handler in self._metric_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(metrics)
                    else:
                        handler(metrics)
                except Exception as e:
                    logger.error(f"Error in metrics handler: {e}")

        except Exception as e:
            logger.error(f"Error collecting metrics for {target.name}: {e}")

    # Alert Management
    async def _evaluate_alert_rule(self, rule: AlertRule):
        """Evaluate alert rule against current metrics."""
        try:
            # This is a simplified implementation
            # In practice, you'd have a proper expression evaluator

            # Get relevant metrics
            metrics_data = {}
            for target_id, metrics in self._device_metrics.items():
                if metrics.cpu_utilization is not None:
                    metrics_data[f"{target_id}.cpu"] = metrics.cpu_utilization
                if metrics.memory_utilization is not None:
                    metrics_data[f"{target_id}.memory"] = metrics.memory_utilization

            # Check if alert should fire
            should_fire = rule.evaluate(metrics_data)

            alert_id = f"{rule.name}"
            existing_alert = self._active_alerts.get(alert_id)

            if should_fire and not existing_alert:
                # Create new alert
                alert = Alert(
                    id=alert_id,
                    rule_name=rule.name,
                    target="system",  # Would be more specific in practice
                    severity=rule.severity,
                    message=f"Alert rule '{rule.name}' triggered",
                )

                self._active_alerts[alert_id] = alert
                await self._fire_alert(alert)

            elif not should_fire and existing_alert:
                # Resolve alert
                existing_alert.resolve()
                await self._resolve_alert(existing_alert)
                del self._active_alerts[alert_id]

        except Exception as e:
            logger.error(f"Error evaluating alert rule {rule.name}: {e}")

    async def _fire_alert(self, alert: Alert):
        """Fire new alert."""
        logger.warning(f"ALERT FIRED: {alert.rule_name} - {alert.message}")

        # Notify handlers
        for handler in self._alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

    async def _resolve_alert(self, alert: Alert):
        """Resolve alert."""
        logger.info(
            f"ALERT RESOLVED: {alert.rule_name} - Duration: {alert.duration:.2f}s"
        )

    async def _check_auto_resolve(self):
        """Check for alerts that should auto-resolve."""
        now = datetime.now(UTC)
        to_resolve = []

        for alert in self._active_alerts.values():
            rule = self._alert_rules.get(alert.rule_name)
            if rule and rule.auto_resolve:
                if (now - alert.created_at).total_seconds() > rule.auto_resolve_timeout:
                    to_resolve.append(alert)

        for alert in to_resolve:
            alert.resolve()
            await self._resolve_alert(alert)
            del self._active_alerts[alert.id]

    # Data Management
    async def _cleanup_old_data(self):
        """Clean up old monitoring data."""
        try:
            cutoff_time = datetime.now(UTC).timestamp() - self.config.metric_retention

            # Clean up metrics
            for metric_key in self._metrics:
                metric_queue = self._metrics[metric_key]
                while (
                    metric_queue
                    and metric_queue[0]["timestamp"].timestamp() < cutoff_time
                ):
                    metric_queue.popleft()

            logger.debug("Completed monitoring data cleanup")

        except Exception as e:
            logger.error(f"Error during data cleanup: {e}")

    # Event Handlers
    def add_metric_handler(self, handler: Callable):
        """Add metric collection handler."""
        self._metric_handlers.append(handler)

    def add_alert_handler(self, handler: Callable):
        """Add alert handler."""
        self._alert_handlers.append(handler)

    def add_health_handler(self, handler: Callable):
        """Add health check handler."""
        self._health_handlers.append(handler)

    # Query Interface
    def get_health_result(self, check_name: str) -> Optional[HealthCheckResult]:
        """Get latest health check result."""
        return self._health_results.get(check_name)

    def get_device_metrics(self, device_id: str) -> Optional[DeviceMetrics]:
        """Get latest device metrics."""
        return self._device_metrics.get(device_id)

    def get_active_alerts(self) -> list[Alert]:
        """Get all active alerts."""
        return list(self._active_alerts.values())

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID."""
        return self._active_alerts.get(alert_id)

    def get_historical_metrics(
        self, target_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get historical metrics for target."""
        metric_key = f"{target_id}.metrics"
        metrics = self._metrics.get(metric_key, deque())
        return list(metrics)[-limit:]

    # Statistics
    def get_monitoring_stats(self) -> dict[str, Any]:
        """Get monitoring system statistics."""
        return {
            "running": self._running,
            "targets": len(self._targets),
            "health_checks": len(self._health_checks),
            "alert_rules": len(self._alert_rules),
            "active_alerts": len(self._active_alerts),
            "devices_with_metrics": len(self._device_metrics),
            "total_metrics_series": len(self._metrics),
        }
