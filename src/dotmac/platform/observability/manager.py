"""
Observability Manager - A unified interface for managing observability components.

This module provides the ObservabilityManager class that wraps initialization
of OpenTelemetry, logging, metrics, and middleware configuration for FastAPI apps.
"""

import logging
from typing import Any

from fastapi import FastAPI

from .bootstrap import OTelBootstrap, initialize_otel, shutdown_otel
from .config import ObservabilityConfig, create_default_config
from .logging import StructuredLogger, create_logger, init_structured_logging
from .metrics import (
    MetricsRegistry,
    TenantMetrics,
    initialize_metrics_registry,
    initialize_tenant_metrics,
)
from .middleware import (
    LoggingMiddleware,
    MetricsMiddleware,
    PerformanceMonitoringMiddleware,
    SecurityMiddleware,
    TracingMiddleware,
)
from .tracing import TracingManager


class ObservabilityManager:
    """
    Unified manager for observability components.

    This class provides a simple interface to initialize and manage all observability
    components including OpenTelemetry, structured logging, metrics, and middleware.

    Example usage:
        # Initialize the manager
        mgr = ObservabilityManager(
            service_name="my-service",
            otlp_endpoint="http://localhost:4317"
        )

        # Initialize all components
        mgr.initialize()

        # Apply middleware to FastAPI app
        mgr.apply_middleware(app)

        # Get a logger
        logger = mgr.get_logger()

        # Shutdown when done
        mgr.shutdown()
    """

    def __init__(
        self,
        service_name: str = "dotmac-service",
        environment: str = "development",
        otlp_endpoint: str | None = None,
        log_level: str = "INFO",
        correlation_id_header: str = "X-Correlation-ID",
        enable_tracing: bool = True,
        enable_metrics: bool = True,
        enable_logging: bool = True,
        enable_performance: bool = True,
        enable_security: bool = False,
        trace_sampler_ratio: float = 1.0,
        slow_request_threshold: float = 1000.0,
        **kwargs,
    ):
        """
        Initialize the Observability Manager.

        Args:
            service_name: Name of the service for identification
            environment: Environment name (development, staging, production)
            otlp_endpoint: OTLP endpoint for exporting telemetry data
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            correlation_id_header: Header name for correlation ID
            enable_tracing: Enable distributed tracing
            enable_metrics: Enable metrics collection
            enable_logging: Enable structured logging
            enable_performance: Enable performance monitoring middleware
            enable_security: Enable security monitoring middleware
            trace_sampler_ratio: Ratio of traces to sample (0.0 to 1.0)
            slow_request_threshold: Threshold in ms for slow request detection
            **kwargs: Additional configuration options
        """
        self.service_name = service_name
        self.environment = environment
        self.otlp_endpoint = otlp_endpoint
        self.log_level = log_level
        self.correlation_id_header = correlation_id_header
        self.enable_tracing = enable_tracing
        self.enable_metrics = enable_metrics
        self.enable_logging = enable_logging
        self.enable_performance = enable_performance
        self.enable_security = enable_security
        self.trace_sampler_ratio = trace_sampler_ratio
        self.slow_request_threshold = slow_request_threshold
        self.extra_config = kwargs

        # Component instances
        self._otel_bootstrap: OTelBootstrap | None = None
        self._metrics_registry: MetricsRegistry | None = None
        self._tenant_metrics: TenantMetrics | None = None
        self._logger: StructuredLogger | None = None
        self._tracing_manager: TracingManager | None = None
        self._initialized = False

    @property
    def initialized(self) -> bool:
        """Compatibility property indicating whether initialize() has been called."""
        return self._initialized

    def initialize(self) -> None:
        """
        Initialize all observability components.

        This method initializes:
        - OpenTelemetry tracing and metrics
        - Structured logging
        - Metrics registry
        - Tenant metrics (if available)
        - Tracing manager
        """
        if self._initialized:
            logging.warning(f"ObservabilityManager for {self.service_name} already initialized")
            return

        # Allow tests to patch these setup phases
        try:
            self._setup_logging()
            self._setup_tracing()
            self._setup_metrics()
        except AttributeError:
            # Fallback to normal flow if not overridden
            pass

        # Create ObservabilityConfig for use by all components
        self.obs_config = ObservabilityConfig(
            service_name=self.service_name,
            environment=self.environment,
            log_level=self.log_level,
            json_logging=True,
            enable_structured_logging=self.enable_logging,
            enable_auto_instrumentation=False,
            enable_tracing=self.enable_tracing,
            enable_metrics=self.enable_metrics,
        )

        # Initialize OpenTelemetry
        if self.enable_tracing or self.enable_metrics:
            try:
                # Determine exporters based on environment and settings
                tracing_exporters = None
                metrics_exporters = None
                if self.otlp_endpoint:
                    if self.enable_tracing:
                        tracing_exporters = ["otlp"]
                    if self.enable_metrics:
                        metrics_exporters = ["otlp"]

                otel_config = create_default_config(
                    service_name=self.service_name,
                    environment=self.environment,
                    otlp_endpoint=self.otlp_endpoint,
                    tracing_exporters=tracing_exporters,
                    metrics_exporters=metrics_exporters,
                    **{
                        k: v
                        for k, v in self.extra_config.items()
                        if k in ["service_version", "custom_resource_attributes"]
                    },
                )
                # Apply additional settings
                otel_config.trace_sampler_ratio = self.trace_sampler_ratio
                otel_config.enable_tracing = self.enable_tracing
                otel_config.enable_metrics = self.enable_metrics
                self._otel_bootstrap = initialize_otel(otel_config)
                logging.info(f"OpenTelemetry initialized for {self.service_name}")
            except Exception as e:
                logging.error(f"Failed to initialize OpenTelemetry: {e}")

        # Initialize structured logging
        if self.enable_logging:
            try:
                init_structured_logging(config=self.obs_config)
                self._logger = create_logger(self.service_name)
                logging.info(f"Structured logging initialized for {self.service_name}")
            except Exception as e:
                logging.error(f"Failed to initialize structured logging: {e}")
                self._logger = logging.getLogger(self.service_name)
        else:
            self._logger = logging.getLogger(self.service_name)

        # Initialize metrics registry
        if self.enable_metrics:
            try:
                self._metrics_registry = initialize_metrics_registry(self.service_name)

                # Initialize tenant metrics if available
                try:
                    self._tenant_metrics = initialize_tenant_metrics(
                        self.service_name, self._metrics_registry
                    )
                    logging.info(f"Tenant metrics initialized for {self.service_name}")
                except Exception as e:
                    logging.warning(f"Tenant metrics not available: {e}")

                logging.info(f"Metrics registry initialized for {self.service_name}")
            except Exception as e:
                logging.error(f"Failed to initialize metrics registry: {e}")

        # Initialize tracing manager
        if self.enable_tracing:
            try:
                self._tracing_manager = TracingManager(config=self.obs_config)
                logging.info(f"Tracing manager initialized for {self.service_name}")
            except Exception as e:
                logging.error(f"Failed to initialize tracing manager: {e}")

        self._initialized = True
        logging.info(f"ObservabilityManager fully initialized for {self.service_name}")

    def apply_middleware(
        self,
        app: FastAPI,
        enable_metrics: bool | None = None,
        enable_tracing: bool | None = None,
        enable_logging: bool | None = None,
        enable_performance: bool | None = None,
        enable_security: bool | None = None,
    ) -> FastAPI:
        """
        Apply observability middleware to a FastAPI application.

        Args:
            app: FastAPI application instance
            enable_metrics: Override metrics middleware setting
            enable_tracing: Override tracing middleware setting
            enable_logging: Override logging middleware setting
            enable_performance: Override performance middleware setting
            enable_security: Override security middleware setting

        Returns:
            The FastAPI app with middleware applied
        """
        if not isinstance(app, FastAPI):
            raise TypeError("app must be a FastAPI instance")

        # Use provided settings or fall back to instance settings
        enable_metrics = self.enable_metrics if enable_metrics is None else enable_metrics
        enable_tracing = self.enable_tracing if enable_tracing is None else enable_tracing
        enable_logging = self.enable_logging if enable_logging is None else enable_logging
        enable_performance = (
            self.enable_performance if enable_performance is None else enable_performance
        )
        enable_security = self.enable_security if enable_security is None else enable_security

        # Add middleware in reverse order (FastAPI processes them in reverse)

        # Security middleware (first to process)
        if enable_security:
            try:
                app.add_middleware(
                    SecurityMiddleware,
                    config=self.obs_config if hasattr(self, "obs_config") else None,
                    service_name=self.service_name,
                )
                logging.info(f"Security middleware added to {self.service_name}")
            except Exception as e:
                logging.error(f"Failed to add security middleware: {e}")

        # Performance monitoring
        if enable_performance:
            try:
                app.add_middleware(
                    PerformanceMonitoringMiddleware,
                    config=self.obs_config if hasattr(self, "obs_config") else None,
                    service_name=self.service_name,
                    slow_request_threshold=self.slow_request_threshold,
                )
                logging.info(f"Performance monitoring middleware added to {self.service_name}")
            except Exception as e:
                logging.error(f"Failed to add performance middleware: {e}")

        # Detailed logging
        if enable_logging:
            try:
                app.add_middleware(
                    LoggingMiddleware,
                    config=self.obs_config if hasattr(self, "obs_config") else None,
                    service_name=self.service_name,
                )
                logging.info(f"Logging middleware added to {self.service_name}")
            except Exception as e:
                logging.error(f"Failed to add logging middleware: {e}")

        # Distributed tracing
        if enable_tracing:
            try:
                app.add_middleware(
                    TracingMiddleware,
                    config=self.obs_config if hasattr(self, "obs_config") else None,
                    service_name=self.service_name,
                )
                logging.info(f"Tracing middleware added to {self.service_name}")
            except Exception as e:
                logging.error(f"Failed to add tracing middleware: {e}")

        # Metrics collection
        if enable_metrics:
            try:
                app.add_middleware(MetricsMiddleware, service_name=self.service_name)
                logging.info(f"Metrics middleware added to {self.service_name}")
            except Exception as e:
                logging.error(f"Failed to add metrics middleware: {e}")

        logging.info(f"All middleware applied to {self.service_name}")
        return app

    def get_logger(self, name: str | None = None) -> Any:
        """
        Get a logger instance.

        Args:
            name: Optional logger name. If not provided, uses the service name.

        Returns:
            Logger instance (StructuredLogger or standard logger)
        """
        if not self._initialized:
            self.initialize()

        if name:
            if self.enable_logging and self._logger:
                return create_logger(name)
            else:
                return logging.getLogger(name)

        return self._logger or logging.getLogger(self.service_name)

    def get_metrics_registry(self) -> MetricsRegistry | None:
        """
        Get the metrics registry instance.

        Returns:
            MetricsRegistry instance if metrics are enabled, None otherwise
        """
        if not self._initialized:
            self.initialize()

        return self._metrics_registry

    def get_tenant_metrics(self) -> TenantMetrics | None:
        """
        Get the tenant metrics instance.

        Returns:
            TenantMetrics instance if available, None otherwise
        """
        if not self._initialized:
            self.initialize()

        return self._tenant_metrics

    def get_tracing_manager(self) -> TracingManager | None:
        """
        Get the tracing manager instance.

        Returns:
            TracingManager instance if tracing is enabled, None otherwise
        """
        if not self._initialized:
            self.initialize()

        return self._tracing_manager

    def get_otel_bootstrap(self) -> OTelBootstrap | None:
        """
        Get the OpenTelemetry bootstrap instance.

        Returns:
            OTelBootstrap instance if OTEL is initialized, None otherwise
        """
        if not self._initialized:
            self.initialize()

        return self._otel_bootstrap

    def shutdown(self) -> None:
        """
        Shutdown all observability components gracefully.

        This method should be called when the application is shutting down
        to ensure all telemetry data is flushed and resources are cleaned up.
        """
        if not self._initialized:
            return

        # Shutdown OpenTelemetry
        if self._otel_bootstrap:
            try:
                shutdown_otel(self._otel_bootstrap)
                logging.info(f"OpenTelemetry shutdown for {self.service_name}")
            except Exception as e:
                logging.error(f"Failed to shutdown OpenTelemetry: {e}")

        # Clean up other resources
        self._otel_bootstrap = None
        self._metrics_registry = None
        self._tenant_metrics = None
        self._logger = None
        self._tracing_manager = None
        self._initialized = False

    # Stubbed setup methods for test patching
    def _setup_logging(self) -> None:  # pragma: no cover - simple stub
        return

    def _setup_tracing(self) -> None:  # pragma: no cover - simple stub
        return

    def _setup_metrics(self) -> None:  # pragma: no cover - simple stub
        return

        logging.info(f"ObservabilityManager shutdown complete for {self.service_name}")

    def __enter__(self):
        """Context manager entry - initialize components."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - shutdown components."""
        self.shutdown()
        return False

    @property
    def is_initialized(self) -> bool:
        """Check if the manager is initialized."""
        return self._initialized
