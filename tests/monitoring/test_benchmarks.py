"""
Tests for monitoring benchmarks module.
"""

import asyncio
import time
from datetime import datetime, timedelta, UTC
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Mark module as slow to support fast unit selection
pytestmark = pytest.mark.slow

from dotmac.platform.monitoring.benchmarks import (
    BenchmarkManager,
    BenchmarkMetric,
    BenchmarkResult,
    BenchmarkStatus,
    BenchmarkSuite,
    BenchmarkSuiteConfig,
    BenchmarkType,
    CPUBenchmark,
    MemoryBenchmark,
    NetworkBenchmark,
    PerformanceBenchmark,
)


class TestBenchmarkEnums:
    """Test benchmark enumeration types."""

    def test_benchmark_status_values(self):
        """Test all benchmark status values."""
        assert BenchmarkStatus.PENDING == "pending"
        assert BenchmarkStatus.RUNNING == "running"
        assert BenchmarkStatus.COMPLETED == "completed"
        assert BenchmarkStatus.FAILED == "failed"
        assert BenchmarkStatus.CANCELLED == "cancelled"

    def test_benchmark_type_values(self):
        """Test all benchmark type values."""
        assert BenchmarkType.PERFORMANCE == "performance"
        assert BenchmarkType.LOAD == "load"
        assert BenchmarkType.STRESS == "stress"
        assert BenchmarkType.ENDURANCE == "endurance"
        assert BenchmarkType.SPIKE == "spike"
        assert BenchmarkType.MEMORY == "memory"
        assert BenchmarkType.CPU == "cpu"
        assert BenchmarkType.NETWORK == "network"
        assert BenchmarkType.DATABASE == "database"


class TestBenchmarkMetric:
    """Test BenchmarkMetric dataclass."""

    def test_metric_creation(self):
        """Test creating a benchmark metric."""
        metric = BenchmarkMetric(
            name="response_time", value=125.5, unit="ms", category="performance"
        )

        assert metric.name == "response_time"
        assert metric.value == 125.5
        assert metric.unit == "ms"
        assert metric.category == "performance"
        assert metric.timestamp is not None

    def test_metric_with_metadata(self):
        """Test metric with metadata."""
        metadata = {"percentile": "p95", "method": "GET"}
        metric = BenchmarkMetric(name="latency", value=200, unit="ms", metadata=metadata)

        assert metric.metadata == metadata

    def test_metric_auto_timestamp(self):
        """Test automatic timestamp generation."""
        metric = BenchmarkMetric(name="test", value=1, unit="count")

        assert isinstance(metric.timestamp, datetime)
        assert metric.timestamp <= datetime.now(UTC)


class TestBenchmarkResult:
    """Test BenchmarkResult dataclass."""

    def test_result_creation(self):
        """Test creating a benchmark result."""
        start_time = datetime.now(UTC)
        result = BenchmarkResult(
            id="test-123",
            name="Test Benchmark",
            benchmark_type=BenchmarkType.PERFORMANCE,
            status=BenchmarkStatus.PENDING,
            start_time=start_time,
        )

        assert result.id == "test-123"
        assert result.name == "Test Benchmark"
        assert result.benchmark_type == BenchmarkType.PERFORMANCE
        assert result.status == BenchmarkStatus.PENDING
        assert result.start_time == start_time
        assert result.end_time is None
        assert result.duration is None

    def test_result_duration_calculation(self):
        """Test automatic duration calculation."""
        start_time = datetime.now(UTC)
        end_time = start_time + timedelta(seconds=10)

        result = BenchmarkResult(
            id="test-456",
            name="Test",
            benchmark_type=BenchmarkType.CPU,
            status=BenchmarkStatus.COMPLETED,
            start_time=start_time,
            end_time=end_time,
        )

        assert result.duration == timedelta(seconds=10)
        assert result.duration_seconds == 10.0

    def test_add_metric(self):
        """Test adding metrics to result."""
        result = BenchmarkResult(
            id="test",
            name="Test",
            benchmark_type=BenchmarkType.MEMORY,
            status=BenchmarkStatus.RUNNING,
            start_time=datetime.now(UTC),
        )

        result.add_metric("memory_used", 512, "MB")
        result.add_metric("allocations", 1000, "count", category="stats")

        assert len(result.metrics) == 2
        assert result.metrics[0].name == "memory_used"
        assert result.metrics[1].category == "stats"

    def test_get_metric(self):
        """Test retrieving a specific metric."""
        result = BenchmarkResult(
            id="test",
            name="Test",
            benchmark_type=BenchmarkType.NETWORK,
            status=BenchmarkStatus.COMPLETED,
            start_time=datetime.now(UTC),
        )

        result.add_metric("latency", 50, "ms")
        result.add_metric("throughput", 1000, "req/s")

        latency = result.get_metric("latency")
        assert latency is not None
        assert latency.value == 50

        missing = result.get_metric("non_existent")
        assert missing is None

    def test_get_metrics_by_category(self):
        """Test retrieving metrics by category."""
        result = BenchmarkResult(
            id="test",
            name="Test",
            benchmark_type=BenchmarkType.LOAD,
            status=BenchmarkStatus.COMPLETED,
            start_time=datetime.now(UTC),
        )

        result.add_metric("cpu", 75, "%", category="resources")
        result.add_metric("memory", 2048, "MB", category="resources")
        result.add_metric("requests", 1000, "count", category="traffic")

        resource_metrics = result.get_metrics_by_category("resources")
        assert len(resource_metrics) == 2
        assert all(m.category == "resources" for m in resource_metrics)


class MockBenchmark(PerformanceBenchmark):
    """Mock benchmark for testing."""

    def __init__(self, name="Mock Benchmark", should_fail=False):
        super().__init__(name, BenchmarkType.PERFORMANCE)
        self.should_fail = should_fail
        self.setup_called = False
        self.execute_called = False
        self.teardown_called = False

    async def setup(self) -> bool:
        self.setup_called = True
        return not self.should_fail

    async def execute(self) -> dict[str, Any]:
        self.execute_called = True
        if self.should_fail:
            raise Exception("Mock benchmark failed")
        return {"test_metric": 100, "success": True}

    async def teardown(self):
        self.teardown_called = True


class TestPerformanceBenchmark:
    """Test abstract PerformanceBenchmark class."""

    @pytest.mark.asyncio
    async def test_benchmark_lifecycle_success(self):
        """Test successful benchmark lifecycle."""
        benchmark = MockBenchmark()

        result = await benchmark.run()

        assert benchmark.setup_called
        assert benchmark.execute_called
        assert benchmark.teardown_called

        assert result.status == BenchmarkStatus.COMPLETED
        assert result.end_time is not None
        assert len(result.metrics) > 0

    @pytest.mark.asyncio
    async def test_benchmark_lifecycle_failure(self):
        """Test benchmark failure handling."""
        benchmark = MockBenchmark(should_fail=True)

        result = await benchmark.run()

        assert benchmark.setup_called
        assert benchmark.teardown_called  # Teardown should still be called

        assert result.status == BenchmarkStatus.FAILED
        assert result.error_message is not None
        assert "Mock benchmark failed" in result.error_message

    @pytest.mark.asyncio
    async def test_benchmark_cancellation(self):
        """Test benchmark cancellation."""

        class SlowBenchmark(MockBenchmark):
            async def execute(self) -> dict[str, Any]:
                await asyncio.sleep(10)  # Long running
                return {}

        benchmark = SlowBenchmark()

        # Start benchmark and cancel it
        task = asyncio.create_task(benchmark.run())
        await asyncio.sleep(0.1)  # Let it start
        task.cancel()

        try:
            result = await task
            assert result.status == BenchmarkStatus.CANCELLED
            assert result.error_message is not None
        except asyncio.CancelledError:
            pass  # Task may raise CancelledError

    @pytest.mark.asyncio
    async def test_benchmark_process_results(self):
        """Test result processing."""
        benchmark = MockBenchmark()

        result = await benchmark.run()

        # Check that raw results were processed into metrics
        test_metric = result.get_metric("test_metric")
        assert test_metric is not None
        assert test_metric.value == 100
        assert test_metric.category == "benchmark"


class TestCPUBenchmark:
    """Test CPU benchmark implementation."""

    @pytest.mark.asyncio
    async def test_cpu_benchmark_execution(self):
        """Test CPU benchmark executes successfully."""
        benchmark = CPUBenchmark(duration_seconds=1, threads=2)

        result = await benchmark.run()

        assert result.status == BenchmarkStatus.COMPLETED
        assert result.get_metric("iterations") is not None
        assert result.get_metric("operations_per_second") is not None
        assert result.get_metric("threads_used") is not None
        assert result.get_metric("threads_used").value == 2

    @pytest.mark.asyncio
    async def test_cpu_benchmark_performance(self):
        """Test CPU benchmark performance measurement."""
        benchmark = CPUBenchmark(duration_seconds=0.5)

        start = time.perf_counter()
        result = await benchmark.run()
        elapsed = time.perf_counter() - start

        # Should run for approximately the specified duration
        assert 0.4 < elapsed < 1.0  # Some tolerance

        ops_metric = result.get_metric("operations_per_second")
        assert ops_metric.value > 0


class TestMemoryBenchmark:
    """Test memory benchmark implementation."""

    @pytest.mark.asyncio
    async def test_memory_benchmark_execution(self):
        """Test memory benchmark executes successfully."""
        benchmark = MemoryBenchmark(allocation_mb=10, iterations=100)

        result = await benchmark.run()

        assert result.status == BenchmarkStatus.COMPLETED
        assert result.get_metric("allocated_chunks") is not None
        assert result.get_metric("allocated_mb") is not None
        assert result.get_metric("allocation_time_seconds") is not None
        assert result.get_metric("access_time_seconds") is not None

    @pytest.mark.asyncio
    async def test_memory_benchmark_allocation(self):
        """Test memory allocation tracking."""
        iterations = 500
        benchmark = MemoryBenchmark(allocation_mb=1, iterations=iterations)

        result = await benchmark.run()

        chunks_metric = result.get_metric("allocated_chunks")
        assert chunks_metric.value == iterations

        # Memory should be cleared after teardown
        assert len(benchmark.allocated_data) == 0


class TestNetworkBenchmark:
    """Test network benchmark implementation."""

    @pytest.mark.asyncio
    @patch("asyncio.open_connection")
    async def test_network_benchmark_success(self, mock_open_connection):
        """Test network benchmark with successful connections."""
        # Mock successful connection
        mock_reader = Mock()
        mock_writer = Mock()
        mock_writer.close = Mock()
        mock_writer.wait_closed = AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)

        benchmark = NetworkBenchmark(target_host="test.local", port=80, iterations=5)

        result = await benchmark.run()

        assert result.status == BenchmarkStatus.COMPLETED
        assert result.get_metric("successful_connections").value == 5
        assert result.get_metric("success_rate").value == 1.0
        assert result.get_metric("average_latency_ms") is not None

    @pytest.mark.asyncio
    @patch("asyncio.open_connection")
    async def test_network_benchmark_failures(self, mock_open_connection):
        """Test network benchmark with connection failures."""
        # Mock connection failures
        mock_open_connection.side_effect = ConnectionRefusedError("Connection refused")

        benchmark = NetworkBenchmark(target_host="unreachable.local", port=9999, iterations=3)

        result = await benchmark.run()

        assert result.status == BenchmarkStatus.COMPLETED
        assert result.get_metric("successful_connections").value == 0
        assert result.get_metric("success_rate").value == 0


class TestBenchmarkSuite:
    """Test benchmark suite functionality."""

    @pytest.mark.asyncio
    async def test_suite_sequential_execution(self):
        """Test sequential benchmark execution in suite."""
        config = BenchmarkSuiteConfig(name="Test Suite", parallel_execution=False)
        suite = BenchmarkSuite(config)

        # Add benchmarks
        benchmark1 = MockBenchmark("Benchmark 1")
        benchmark2 = MockBenchmark("Benchmark 2")
        suite.add_benchmark(benchmark1)
        suite.add_benchmark(benchmark2)

        results = await suite.run_all()

        assert len(results) == 2
        assert all(r.status == BenchmarkStatus.COMPLETED for r in results)
        assert benchmark1.execute_called
        assert benchmark2.execute_called

    @pytest.mark.asyncio
    async def test_suite_parallel_execution(self):
        """Test parallel benchmark execution in suite."""
        config = BenchmarkSuiteConfig(name="Parallel Suite", parallel_execution=True)
        suite = BenchmarkSuite(config)

        # Add benchmarks
        for i in range(3):
            suite.add_benchmark(MockBenchmark(f"Benchmark {i}"))

        results = await suite.run_all()

        assert len(results) == 3
        assert all(r.status == BenchmarkStatus.COMPLETED for r in results)

    @pytest.mark.asyncio
    async def test_suite_with_failures(self):
        """Test suite execution with failing benchmarks."""
        config = BenchmarkSuiteConfig(name="Mixed Suite", retry_failed=False)
        suite = BenchmarkSuite(config)

        suite.add_benchmark(MockBenchmark("Success"))
        suite.add_benchmark(MockBenchmark("Failure", should_fail=True))

        results = await suite.run_all()

        assert len(results) == 2
        assert results[0].status == BenchmarkStatus.COMPLETED
        assert results[1].status == BenchmarkStatus.FAILED

    @pytest.mark.asyncio
    async def test_suite_retry_logic(self):
        """Test suite retry logic for failed benchmarks."""

        class RetryableBenchmark(MockBenchmark):
            def __init__(self):
                super().__init__("Retryable")
                self.attempt = 0

            async def execute(self) -> dict[str, Any]:
                self.attempt += 1
                if self.attempt == 1:
                    raise Exception("First attempt fails")
                return {"success": True}

        config = BenchmarkSuiteConfig(name="Retry Suite", retry_failed=True, retry_count=2)
        suite = BenchmarkSuite(config)

        benchmark = RetryableBenchmark()
        suite.add_benchmark(benchmark)

        results = await suite.run_all()

        assert len(results) == 1
        assert results[0].status == BenchmarkStatus.COMPLETED
        assert benchmark.attempt == 2  # Failed once, succeeded on retry

    @pytest.mark.asyncio
    async def test_suite_timeout_handling(self):
        """Test suite timeout handling."""

        class SlowBenchmark(MockBenchmark):
            async def execute(self) -> dict[str, Any]:
                await asyncio.sleep(10)
                return {}

        config = BenchmarkSuiteConfig(name="Timeout Suite", timeout_seconds=1)
        suite = BenchmarkSuite(config)
        suite.add_benchmark(SlowBenchmark())

        results = await suite.run_all()

        assert len(results) == 1
        assert results[0].status == BenchmarkStatus.FAILED
        assert "timed out" in results[0].error_message.lower()

    def test_suite_summary_stats(self):
        """Test suite summary statistics."""
        config = BenchmarkSuiteConfig(name="Stats Suite")
        suite = BenchmarkSuite(config)

        # Manually add results for testing
        suite.results = [
            BenchmarkResult(
                id="1",
                name="Test1",
                benchmark_type=BenchmarkType.CPU,
                status=BenchmarkStatus.COMPLETED,
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC) + timedelta(seconds=5),
            ),
            BenchmarkResult(
                id="2",
                name="Test2",
                benchmark_type=BenchmarkType.MEMORY,
                status=BenchmarkStatus.FAILED,
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC) + timedelta(seconds=3),
            ),
        ]

        # Add metrics
        suite.results[0].add_metric("test", 100, "units")

        stats = suite.get_summary_stats()

        assert stats["total_benchmarks"] == 2
        assert stats["completed"] == 1
        assert stats["failed"] == 1
        assert stats["success_rate"] == 0.5
        assert stats["total_metrics"] == 1


class TestBenchmarkManager:
    """Test benchmark manager functionality."""

    @pytest.mark.asyncio
    async def test_manager_run_benchmark(self):
        """Test running a single benchmark through manager."""
        manager = BenchmarkManager()
        benchmark = MockBenchmark()

        result = await manager.run_benchmark(benchmark)

        assert result.status == BenchmarkStatus.COMPLETED
        assert result in manager.benchmark_history

    @pytest.mark.asyncio
    async def test_manager_active_benchmarks(self):
        """Test tracking active benchmarks."""
        manager = BenchmarkManager()

        class SlowBenchmark(MockBenchmark):
            async def execute(self) -> dict[str, Any]:
                await asyncio.sleep(0.5)
                return {}

        benchmark = SlowBenchmark()

        # Start benchmark
        task = asyncio.create_task(manager.run_benchmark(benchmark))
        await asyncio.sleep(0.1)  # Let it start

        # Check active benchmarks
        active = manager.get_active_benchmarks()
        assert len(active) > 0

        # Wait for completion
        await task

        # Should no longer be active
        active = manager.get_active_benchmarks()
        assert len(active) == 0

    @pytest.mark.asyncio
    async def test_manager_cancel_benchmark(self):
        """Test cancelling a running benchmark."""
        manager = BenchmarkManager()

        class SlowBenchmark(MockBenchmark):
            async def execute(self) -> dict[str, Any]:
                await asyncio.sleep(10)
                return {}

        # Manually start and track benchmark
        benchmark = SlowBenchmark()
        task = asyncio.create_task(benchmark.run())
        task_id = "test-task"
        manager.active_benchmarks[task_id] = task

        # Cancel it
        result = await manager.cancel_benchmark(task_id)

        assert result is True
        assert task_id not in manager.active_benchmarks

    def test_manager_register_suite(self):
        """Test registering benchmark suites."""
        manager = BenchmarkManager()
        config = BenchmarkSuiteConfig(name="Test Suite")
        suite = BenchmarkSuite(config)

        manager.register_suite(suite)

        assert "Test Suite" in manager.suites
        assert manager.suites["Test Suite"] == suite

    @pytest.mark.asyncio
    async def test_manager_run_suite(self):
        """Test running a registered suite."""
        manager = BenchmarkManager()

        config = BenchmarkSuiteConfig(name="Test Suite")
        suite = BenchmarkSuite(config)
        suite.add_benchmark(MockBenchmark())

        manager.register_suite(suite)

        results = await manager.run_suite("Test Suite")

        assert len(results) == 1
        assert all(r in manager.benchmark_history for r in results)

    @pytest.mark.asyncio
    async def test_manager_history_filtering(self):
        """Test benchmark history filtering."""
        manager = BenchmarkManager()

        # Add various results to history
        manager.benchmark_history = [
            BenchmarkResult(
                id="1",
                name="CPU Test",
                benchmark_type=BenchmarkType.CPU,
                status=BenchmarkStatus.COMPLETED,
                start_time=datetime.now(UTC) - timedelta(hours=2),
            ),
            BenchmarkResult(
                id="2",
                name="Memory Test",
                benchmark_type=BenchmarkType.MEMORY,
                status=BenchmarkStatus.FAILED,
                start_time=datetime.now(UTC) - timedelta(hours=1),
            ),
            BenchmarkResult(
                id="3",
                name="CPU Test 2",
                benchmark_type=BenchmarkType.CPU,
                status=BenchmarkStatus.COMPLETED,
                start_time=datetime.now(UTC),
            ),
        ]

        # Filter by type
        cpu_results = manager.get_benchmark_history(benchmark_type=BenchmarkType.CPU)
        assert len(cpu_results) == 2

        # Filter by status
        failed_results = manager.get_benchmark_history(status=BenchmarkStatus.FAILED)
        assert len(failed_results) == 1

        # Limit results
        limited_results = manager.get_benchmark_history(limit=1)
        assert len(limited_results) == 1
        assert limited_results[0].id == "3"  # Most recent

    def test_manager_clear_history(self):
        """Test clearing benchmark history."""
        manager = BenchmarkManager()

        # Add some history
        manager.benchmark_history = [
            BenchmarkResult(
                id="1",
                name="Test",
                benchmark_type=BenchmarkType.CPU,
                status=BenchmarkStatus.COMPLETED,
                start_time=datetime.now(UTC),
            )
        ]

        manager.clear_history()

        assert len(manager.benchmark_history) == 0
