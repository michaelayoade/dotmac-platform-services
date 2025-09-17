"""
Observability logging/tracing slice tests: no external exporters.
"""

from dotmac.platform.observability.logging import LogLevel, configure_logging, get_logger
from dotmac.platform.observability.tracing import trace_operation


def test_configure_logging_and_get_logger():
    configure_logging(level=LogLevel.INFO)
    logger = get_logger("slice-test")
    assert logger and logger.name == "slice-test"


def test_trace_operation_decorator():
    @trace_operation("slice-op")
    def add(a, b):
        return a + b

    assert add(2, 3) == 5
