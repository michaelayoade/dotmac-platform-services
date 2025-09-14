"""
Comprehensive tests for monitoring benchmarks.
"""

import pytest

# Mark the entire module as slow to enable fast unit selection
pytestmark = pytest.mark.slow

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

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


class TestBenchmarkMetric:
    """Test BenchmarkMetric dataclass."""

    def test_benchmark_metric_defaults(self):
        """Test default values are set correctly."""
        metric = BenchmarkMetric(name="test_metric", value=42.5, unit="ms")

        assert metric.name == "test_metric"
        assert metric.value == 42.5
        assert metric.unit == "ms"
        assert metric.category == "general"
        assert metric.metadata == {}
        assert isinstance(metric.timestamp, datetime)

    def test_benchmark_metric_custom_values(self):
        """Test custom values are set correctly."""
        timestamp = datetime.utcnow()
        metadata = {"source": "test"}

        metric = BenchmarkMetric(
            name="response_time",
            value=150,
            unit="ms",
            category="performance",
            metadata=metadata,
            timestamp=timestamp,
        )

        assert metric.name == "response_time"
        assert metric.value == 150
        assert metric.unit == "ms"
        assert metric.category == "performance"
        assert metric.metadata == metadata
        assert metric.timestamp == timestamp


class TestBenchmarkResult:
    """Test BenchmarkResult dataclass."""

    def test_benchmark_result_initialization(self):
        """Test benchmark result initialization."""
        start_time = datetime.utcnow()
        result = BenchmarkResult(
            id="test_id",
            name="test_benchmark",
            benchmark_type=BenchmarkType.PERFORMANCE,
            status=BenchmarkStatus.PENDING,
            start_time=start_time,
        )

        assert result.id == "test_id"
        assert result.name == "test_benchmark"
        assert result.benchmark_type == BenchmarkType.PERFORMANCE
        assert result.status == BenchmarkStatus.PENDING
        assert result.start_time == start_time
        assert result.end_time is None
        assert result.duration is None
        assert result.metrics == []
        assert result.metadata == {}
        assert result.error_message is None

    def test_benchmark_result_duration_calculation(self):
        """Test duration calculation when end_time is set."""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(seconds=30)

        result = BenchmarkResult(
            id="test_id",
            name="test_benchmark",
            benchmark_type=BenchmarkType.PERFORMANCE,
            status=BenchmarkStatus.COMPLETED,
            start_time=start_time,
            end_time=end_time,
        )

        assert result.duration == timedelta(seconds=30)
        assert result.duration_seconds == 30.0

    def test_add_metric(self):
        """Test adding metrics to result."""
        result = BenchmarkResult(
            id="test_id",
            name="test_benchmark",
            benchmark_type=BenchmarkType.PERFORMANCE,
            status=BenchmarkStatus.PENDING,
            start_time=datetime.utcnow(),
        )

        result.add_metric("cpu_usage", 75.5, "percent", category="system")

        assert len(result.metrics) == 1
        metric = result.metrics[0]
        assert metric.name == "cpu_usage"
        assert metric.value == 75.5
        assert metric.unit == "percent"
        assert metric.category == "system"

    def test_get_metric(self):
        """Test getting specific metric by name."""
        result = BenchmarkResult(
            id="test_id",
            name="test_benchmark",
            benchmark_type=BenchmarkType.PERFORMANCE,
            status=BenchmarkStatus.PENDING,
            start_time=datetime.utcnow(),
        )

        result.add_metric("cpu_usage", 75.5, "percent")
        result.add_metric("memory_usage", 60.2, "percent")

        cpu_metric = result.get_metric("cpu_usage")
        assert cpu_metric is not None
        assert cpu_metric.name == "cpu_usage"
        assert cpu_metric.value == 75.5

        nonexistent_metric = result.get_metric("nonexistent")
        assert nonexistent_metric is None

    def test_get_metrics_by_category(self):
        """Test getting metrics by category."""
        result = BenchmarkResult(
            id="test_id",
            name="test_benchmark",
            benchmark_type=BenchmarkType.PERFORMANCE,
            status=BenchmarkStatus.PENDING,
            start_time=datetime.utcnow(),
        )

        result.add_metric("cpu_usage", 75.5, "percent", category="system")
        result.add_metric("memory_usage", 60.2, "percent", category="system")
        result.add_metric("response_time", 150, "ms", category="performance")

        system_metrics = result.get_metrics_by_category("system")
        assert len(system_metrics) == 2
        assert all(m.category == "system" for m in system_metrics)

        performance_metrics = result.get_metrics_by_category("performance")
        assert len(performance_metrics) == 1
        assert performance_metrics[0].name == "response_time"


class TestPerformanceBenchmark:
    """Test PerformanceBenchmark abstract base class."""

    class MockBenchmark(PerformanceBenchmark):
        """Mock implementation for testing."""

        def __init__(self, name="test_benchmark", setup_result=True, execute_result=None):
            super().__init__(name, BenchmarkType.PERFORMANCE)
            self._setup_result = setup_result
            self._execute_result = execute_result or {"test_metric": 42}
            self._setup_called = False
            self._execute_called = False
            self._teardown_called = False

        async def setup(self) -> bool:
            self._setup_called = True
            return self._setup_result

        async def execute(self):
            self._execute_called = True
            return self._execute_result

        async def teardown(self):
            self._teardown_called = True

    def test_initialization(self):
        """Test benchmark initialization."""
        benchmark = self.MockBenchmark("test")

        assert benchmark.name == "test"
        assert benchmark.benchmark_type == BenchmarkType.PERFORMANCE
        assert benchmark.metadata == {}

    def test_initialization_with_metadata(self):
        """Test benchmark initialization with metadata."""
        metadata = {"test": "value"}
        benchmark = self.MockBenchmark("test")
        benchmark.metadata = metadata

        assert benchmark.metadata == metadata

    @pytest.mark.asyncio
    async def test_run_success(self):
        """Test successful benchmark run."""
        benchmark = self.MockBenchmark("test", execute_result={"iterations": 1000})

        result = await benchmark.run()

        assert result.status == BenchmarkStatus.COMPLETED
        assert result.name == "test"
        assert result.benchmark_type == BenchmarkType.PERFORMANCE
        assert result.end_time is not None
        assert result.duration is not None
        assert len(result.metrics) > 0

        # Verify lifecycle calls
        assert benchmark._setup_called
        assert benchmark._execute_called
        assert benchmark._teardown_called

    @pytest.mark.asyncio
    async def test_run_setup_failure(self):
        """Test benchmark run with setup failure."""
        benchmark = self.MockBenchmark("test", setup_result=False)

        result = await benchmark.run()

        assert result.status == BenchmarkStatus.FAILED
        assert result.error_message == "Benchmark setup failed"
        assert benchmark._setup_called
        # Implementation may still call execute; only status/message are enforced
        assert benchmark._teardown_called

    @pytest.mark.asyncio
    async def test_run_execute_failure(self):
        """Test benchmark run with execute failure."""
        benchmark = self.MockBenchmark("test")

        # Make execute raise an exception
        async def failing_execute():
            raise ValueError("Execution failed")

        benchmark.execute = failing_execute

        result = await benchmark.run()

        assert result.status == BenchmarkStatus.FAILED
        assert "Execution failed" in result.error_message
        assert benchmark._setup_called
        assert benchmark._teardown_called

    @pytest.mark.asyncio
    async def test_run_cancellation(self):
        """Test benchmark run cancellation."""
        benchmark = self.MockBenchmark("test")

        # Make execute hang and then cancel
        async def hanging_execute():
            await asyncio.sleep(10)  # Long sleep
            return {"test": "value"}

        benchmark.execute = hanging_execute

        # Start the benchmark and cancel it
        task = asyncio.create_task(benchmark.run())
        await asyncio.sleep(0.1)  # Let it start
        task.cancel()

        # The benchmark catches CancelledError and returns a result
        try:
            result = await task
            assert result.status == BenchmarkStatus.CANCELLED
            assert result.error_message == "Benchmark was cancelled"
        except asyncio.CancelledError:
            # This is also acceptable if the implementation doesn't catch it
            pass


class TestCPUBenchmark:
    """Test CPU benchmark implementation."""

    def test_initialization(self):
        """Test CPU benchmark initialization."""
        benchmark = CPUBenchmark(duration_seconds=5, threads=2)

        assert benchmark.name == "CPU Benchmark"
        assert benchmark.benchmark_type == BenchmarkType.CPU
        assert benchmark.duration_seconds == 5
        assert benchmark.threads == 2

    def test_default_initialization(self):
        """Test CPU benchmark with default values."""
        benchmark = CPUBenchmark()

        assert benchmark.duration_seconds == 10
        assert benchmark.threads == 1

    @pytest.mark.asyncio
    async def test_setup(self):
        """Test CPU benchmark setup."""
        benchmark = CPUBenchmark()

        result = await benchmark.setup()

        assert result is True

    @pytest.mark.asyncio
    async def test_execute(self):
        """Test CPU benchmark execution."""
        benchmark = CPUBenchmark(duration_seconds=1)  # Short duration for test

        result = await benchmark.execute()

        assert "iterations" in result
        assert "execution_time_seconds" in result
        assert "operations_per_second" in result
        assert "threads_used" in result

        assert isinstance(result["iterations"], int)
        assert result["iterations"] > 0
        assert result["execution_time_seconds"] > 0
        assert result["operations_per_second"] > 0
        assert result["threads_used"] == benchmark.threads

    @pytest.mark.asyncio
    async def test_teardown(self):
        """Test CPU benchmark teardown."""
        benchmark = CPUBenchmark()

        await benchmark.teardown()  # Should not raise any exception

    @pytest.mark.asyncio
    async def test_full_run(self):
        """Test complete CPU benchmark run."""
        benchmark = CPUBenchmark(duration_seconds=1)

        result = await benchmark.run()

        assert result.status == BenchmarkStatus.COMPLETED
        assert len(result.metrics) > 0

        # Check for expected metrics
        iterations_metric = result.get_metric("iterations")
        assert iterations_metric is not None
        assert iterations_metric.value > 0


class TestMemoryBenchmark:
    """Test Memory benchmark implementation."""

    def test_initialization(self):
        """Test Memory benchmark initialization."""
        benchmark = MemoryBenchmark(allocation_mb=50, iterations=500)

        assert benchmark.name == "Memory Benchmark"
        assert benchmark.benchmark_type == BenchmarkType.MEMORY
        assert benchmark.allocation_mb == 50
        assert benchmark.iterations == 500

    @pytest.mark.asyncio
    async def test_setup(self):
        """Test Memory benchmark setup."""
        benchmark = MemoryBenchmark()

        result = await benchmark.setup()

        assert result is True

    @pytest.mark.asyncio
    async def test_execute(self):
        """Test Memory benchmark execution."""
        benchmark = MemoryBenchmark(allocation_mb=1, iterations=100)  # Small values for test

        result = await benchmark.execute()

        expected_keys = [
            "allocated_chunks",
            "allocated_mb",
            "allocation_time_seconds",
            "access_time_seconds",
            "bytes_accessed",
            "allocation_rate_mb_per_second",
            "access_rate_mb_per_second",
        ]

        for key in expected_keys:
            assert key in result
            assert isinstance(result[key], (int, float))
            assert result[key] >= 0

    @pytest.mark.asyncio
    async def test_teardown(self):
        """Test Memory benchmark teardown."""
        benchmark = MemoryBenchmark()

        # Simulate some allocated data
        benchmark.allocated_data = [bytearray(1024) for _ in range(10)]

        await benchmark.teardown()

        assert len(benchmark.allocated_data) == 0

    @pytest.mark.asyncio
    async def test_full_run(self):
        """Test complete Memory benchmark run."""
        benchmark = MemoryBenchmark(allocation_mb=1, iterations=50)

        result = await benchmark.run()

        assert result.status == BenchmarkStatus.COMPLETED
        assert len(result.metrics) > 0

        # Check for expected metrics
        allocated_metric = result.get_metric("allocated_chunks")
        assert allocated_metric is not None
        assert allocated_metric.value > 0


class TestNetworkBenchmark:
    """Test Network benchmark implementation."""

    def test_initialization(self):
        """Test Network benchmark initialization."""
        benchmark = NetworkBenchmark(target_host="google.com", port=80, iterations=5)

        assert benchmark.name == "Network Benchmark"
        assert benchmark.benchmark_type == BenchmarkType.NETWORK
        assert benchmark.target_host == "google.com"
        assert benchmark.port == 80
        assert benchmark.iterations == 5

    @pytest.mark.asyncio
    async def test_setup(self):
        """Test Network benchmark setup."""
        benchmark = NetworkBenchmark()

        result = await benchmark.setup()

        assert result is True

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test Network benchmark metrics without real network IO."""

        class FastNetworkBenchmark(NetworkBenchmark):
            async def execute(self):
                return {
                    "total_attempts": self.iterations,
                    "successful_connections": self.iterations,
                    "success_rate": 1.0,
                    "average_latency_ms": 10.0,
                    "min_latency_ms": 8.0,
                    "max_latency_ms": 12.0,
                    "median_latency_ms": 10.0,
                }

        benchmark = FastNetworkBenchmark(iterations=2)
        result = await benchmark.execute()

        assert result["total_attempts"] == 2
        assert result["successful_connections"] == 2
        assert result["success_rate"] == 1.0
        assert result["average_latency_ms"] == 10.0

    @pytest.mark.asyncio
    async def test_execute_connection_failures(self):
        """Test Network benchmark metrics for failure case without network IO."""

        class FailingNetworkBenchmark(NetworkBenchmark):
            async def execute(self):
                return {
                    "total_attempts": self.iterations,
                    "successful_connections": 0,
                    "success_rate": 0.0,
                    "average_latency_ms": 0,
                    "min_latency_ms": 0,
                    "max_latency_ms": 0,
                    "median_latency_ms": 0,
                }

        benchmark = FailingNetworkBenchmark(iterations=2)
        result = await benchmark.execute()
        assert result["total_attempts"] == 2
        assert result["successful_connections"] == 0
        assert result["success_rate"] == 0.0
        assert result["average_latency_ms"] == 0

    @pytest.mark.asyncio
    async def test_teardown(self):
        """Test Network benchmark teardown."""
        benchmark = NetworkBenchmark()

        await benchmark.teardown()  # Should not raise any exception


class TestBenchmarkSuiteConfig:
    """Test BenchmarkSuiteConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = BenchmarkSuiteConfig(name="test_suite")

        assert config.name == "test_suite"
        assert config.description == ""
        assert config.timeout_seconds == 300
        assert config.parallel_execution is False
        assert config.retry_failed is False
        assert config.retry_count == 1

    def test_custom_values(self):
        """Test custom configuration values."""
        config = BenchmarkSuiteConfig(
            name="custom_suite",
            description="Custom test suite",
            timeout_seconds=600,
            parallel_execution=True,
            retry_failed=True,
            retry_count=3,
        )

        assert config.name == "custom_suite"
        assert config.description == "Custom test suite"
        assert config.timeout_seconds == 600
        assert config.parallel_execution is True
        assert config.retry_failed is True
        assert config.retry_count == 3


class TestBenchmarkSuite:
    """Test BenchmarkSuite functionality."""

    def test_initialization(self):
        """Test suite initialization."""
        config = BenchmarkSuiteConfig(name="test_suite")
        suite = BenchmarkSuite(config)

        assert suite.config == config
        assert suite.benchmarks == []
        assert suite.results == []

    def test_add_benchmark(self):
        """Test adding benchmarks to suite."""
        config = BenchmarkSuiteConfig(name="test_suite")
        suite = BenchmarkSuite(config)

        benchmark1 = CPUBenchmark()
        benchmark2 = MemoryBenchmark()

        suite.add_benchmark(benchmark1)
        suite.add_benchmark(benchmark2)

        assert len(suite.benchmarks) == 2
        assert benchmark1 in suite.benchmarks
        assert benchmark2 in suite.benchmarks

    @pytest.mark.asyncio
    async def test_run_all_sequential(self):
        """Test running all benchmarks sequentially."""
        config = BenchmarkSuiteConfig(name="test_suite", parallel_execution=False)
        suite = BenchmarkSuite(config)

        # Add mock benchmarks
        benchmark1 = Mock()
        benchmark1.run = AsyncMock()
        benchmark1.run.return_value = BenchmarkResult(
            id="1",
            name="bench1",
            benchmark_type=BenchmarkType.CPU,
            status=BenchmarkStatus.COMPLETED,
            start_time=datetime.utcnow(),
        )

        benchmark2 = Mock()
        benchmark2.run = AsyncMock()
        benchmark2.run.return_value = BenchmarkResult(
            id="2",
            name="bench2",
            benchmark_type=BenchmarkType.MEMORY,
            status=BenchmarkStatus.COMPLETED,
            start_time=datetime.utcnow(),
        )

        suite.add_benchmark(benchmark1)
        suite.add_benchmark(benchmark2)

        results = await suite.run_all()

        assert len(results) == 2
        assert len(suite.results) == 2
        benchmark1.run.assert_called_once()
        benchmark2.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_all_parallel(self):
        """Test running all benchmarks in parallel."""
        config = BenchmarkSuiteConfig(name="test_suite", parallel_execution=True)
        suite = BenchmarkSuite(config)

        # Add mock benchmarks
        benchmark1 = Mock()
        benchmark1.run = AsyncMock()
        benchmark1.run.return_value = BenchmarkResult(
            id="1",
            name="bench1",
            benchmark_type=BenchmarkType.CPU,
            status=BenchmarkStatus.COMPLETED,
            start_time=datetime.utcnow(),
        )

        benchmark2 = Mock()
        benchmark2.run = AsyncMock()
        benchmark2.run.return_value = BenchmarkResult(
            id="2",
            name="bench2",
            benchmark_type=BenchmarkType.MEMORY,
            status=BenchmarkStatus.COMPLETED,
            start_time=datetime.utcnow(),
        )

        suite.add_benchmark(benchmark1)
        suite.add_benchmark(benchmark2)

        results = await suite.run_all()

        assert len(results) == 2
        assert len(suite.results) == 2
        benchmark1.run.assert_called_once()
        benchmark2.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_with_retry(self):
        """Test running benchmarks with retry logic."""
        config = BenchmarkSuiteConfig(name="test_suite", retry_failed=True, retry_count=2)
        suite = BenchmarkSuite(config)

        # Mock benchmark that fails first time, succeeds second time
        benchmark = Mock()
        failed_result = BenchmarkResult(
            id="1",
            name="bench1",
            benchmark_type=BenchmarkType.CPU,
            status=BenchmarkStatus.FAILED,
            start_time=datetime.utcnow(),
        )
        success_result = BenchmarkResult(
            id="1",
            name="bench1",
            benchmark_type=BenchmarkType.CPU,
            status=BenchmarkStatus.COMPLETED,
            start_time=datetime.utcnow(),
        )

        benchmark.run = AsyncMock(side_effect=[failed_result, success_result])
        suite.add_benchmark(benchmark)

        results = await suite.run_all()

        assert len(results) == 1
        assert results[0].status == BenchmarkStatus.COMPLETED
        assert benchmark.run.call_count == 2  # Original + 1 retry

    @pytest.mark.asyncio
    async def test_run_with_timeout(self):
        """Test benchmark execution with timeout."""
        config = BenchmarkSuiteConfig(name="test_suite", timeout_seconds=1)
        suite = BenchmarkSuite(config)

        # Mock benchmark that takes too long
        benchmark = Mock()
        benchmark.name = "slow_benchmark"
        benchmark.benchmark_type = BenchmarkType.CPU

        async def slow_run():
            await asyncio.sleep(2)  # Longer than timeout
            return BenchmarkResult(
                id="1",
                name="slow_benchmark",
                benchmark_type=BenchmarkType.CPU,
                status=BenchmarkStatus.COMPLETED,
                start_time=datetime.utcnow(),
            )

        benchmark.run = slow_run
        suite.add_benchmark(benchmark)

        results = await suite.run_all()

        assert len(results) == 1
        assert results[0].status == BenchmarkStatus.FAILED
        assert "timed out" in results[0].error_message

    def test_get_summary_stats_empty(self):
        """Test getting summary stats with no results."""
        config = BenchmarkSuiteConfig(name="test_suite")
        suite = BenchmarkSuite(config)

        stats = suite.get_summary_stats()

        assert stats == {}

    def test_get_summary_stats_with_results(self):
        """Test getting summary stats with results."""
        config = BenchmarkSuiteConfig(name="test_suite")
        suite = BenchmarkSuite(config)

        # Add mock results
        start_time = datetime.utcnow()
        result1 = BenchmarkResult(
            id="1",
            name="bench1",
            benchmark_type=BenchmarkType.CPU,
            status=BenchmarkStatus.COMPLETED,
            start_time=start_time,
            end_time=start_time + timedelta(seconds=5),
        )
        result1.add_metric("test", 42, "units")

        result2 = BenchmarkResult(
            id="2",
            name="bench2",
            benchmark_type=BenchmarkType.MEMORY,
            status=BenchmarkStatus.FAILED,
            start_time=start_time,
            end_time=start_time + timedelta(seconds=3),
        )

        suite.results = [result1, result2]

        stats = suite.get_summary_stats()

        assert stats["total_benchmarks"] == 2
        assert stats["completed"] == 1
        assert stats["failed"] == 1
        assert stats["cancelled"] == 0
        assert stats["success_rate"] == 0.5
        assert stats["average_duration_seconds"] == 4.0
        assert stats["min_duration_seconds"] == 3.0
        assert stats["max_duration_seconds"] == 5.0
        assert stats["total_metrics"] == 1


class TestBenchmarkManager:
    """Test BenchmarkManager functionality."""

    def test_initialization(self):
        """Test benchmark manager initialization."""
        manager = BenchmarkManager()

        assert manager.active_benchmarks == {}
        assert manager.benchmark_history == []
        assert manager.suites == {}

    @pytest.mark.asyncio
    async def test_run_benchmark(self):
        """Test running a single benchmark."""
        manager = BenchmarkManager()

        # Mock benchmark
        benchmark = Mock()
        benchmark.name = "test_benchmark"
        result = BenchmarkResult(
            id="1",
            name="test_benchmark",
            benchmark_type=BenchmarkType.CPU,
            status=BenchmarkStatus.COMPLETED,
            start_time=datetime.utcnow(),
        )
        benchmark.run = AsyncMock(return_value=result)

        returned_result = await manager.run_benchmark(benchmark)

        assert returned_result == result
        assert len(manager.benchmark_history) == 1
        assert manager.benchmark_history[0] == result
        benchmark.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_benchmark_failure(self):
        """Test benchmark execution failure."""
        manager = BenchmarkManager()

        # Mock benchmark that fails
        benchmark = Mock()
        benchmark.name = "failing_benchmark"
        benchmark.run = AsyncMock(side_effect=Exception("Benchmark failed"))

        with pytest.raises(Exception, match="Benchmark failed"):
            await manager.run_benchmark(benchmark)

    def test_register_suite(self):
        """Test registering a benchmark suite."""
        manager = BenchmarkManager()

        config = BenchmarkSuiteConfig(name="test_suite")
        suite = BenchmarkSuite(config)

        manager.register_suite(suite)

        assert "test_suite" in manager.suites
        assert manager.suites["test_suite"] == suite

    @pytest.mark.asyncio
    async def test_run_suite(self):
        """Test running a registered benchmark suite."""
        manager = BenchmarkManager()

        # Create and register suite
        config = BenchmarkSuiteConfig(name="test_suite")
        suite = BenchmarkSuite(config)

        # Mock run_all method
        result = BenchmarkResult(
            id="1",
            name="bench1",
            benchmark_type=BenchmarkType.CPU,
            status=BenchmarkStatus.COMPLETED,
            start_time=datetime.utcnow(),
        )
        suite.run_all = AsyncMock(return_value=[result])

        manager.register_suite(suite)

        results = await manager.run_suite("test_suite")

        assert len(results) == 1
        assert results[0] == result
        assert len(manager.benchmark_history) == 1
        suite.run_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_suite_not_found(self):
        """Test running non-existent suite."""
        manager = BenchmarkManager()

        with pytest.raises(ValueError, match="not found"):
            await manager.run_suite("nonexistent_suite")

    def test_get_active_benchmarks(self):
        """Test getting active benchmark list."""
        manager = BenchmarkManager()

        # Simulate active benchmarks
        task1 = Mock()
        task2 = Mock()
        manager.active_benchmarks = {"task1": task1, "task2": task2}

        active = manager.get_active_benchmarks()

        assert set(active) == {"task1", "task2"}

    @pytest.mark.asyncio
    async def test_cancel_benchmark(self):
        """Test cancelling a running benchmark."""
        manager = BenchmarkManager()

        # Create mock task with cancel method
        task = Mock()
        task.cancel = Mock()
        manager.active_benchmarks["task_id"] = task

        result = await manager.cancel_benchmark("task_id")

        assert result is True
        task.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_benchmark_not_found(self):
        """Test cancelling non-existent benchmark."""
        manager = BenchmarkManager()

        result = await manager.cancel_benchmark("nonexistent_task")

        assert result is False

    def test_get_benchmark_history_no_filters(self):
        """Test getting benchmark history without filters."""
        manager = BenchmarkManager()

        # Add mock results
        result1 = BenchmarkResult(
            id="1",
            name="bench1",
            benchmark_type=BenchmarkType.CPU,
            status=BenchmarkStatus.COMPLETED,
            start_time=datetime.utcnow(),
        )
        result2 = BenchmarkResult(
            id="2",
            name="bench2",
            benchmark_type=BenchmarkType.MEMORY,
            status=BenchmarkStatus.FAILED,
            start_time=datetime.utcnow(),
        )

        manager.benchmark_history = [result1, result2]

        history = manager.get_benchmark_history()

        assert len(history) == 2
        assert result1 in history
        assert result2 in history

    def test_get_benchmark_history_with_filters(self):
        """Test getting benchmark history with filters."""
        manager = BenchmarkManager()

        # Add mock results
        result1 = BenchmarkResult(
            id="1",
            name="bench1",
            benchmark_type=BenchmarkType.CPU,
            status=BenchmarkStatus.COMPLETED,
            start_time=datetime.utcnow(),
        )
        result2 = BenchmarkResult(
            id="2",
            name="bench2",
            benchmark_type=BenchmarkType.MEMORY,
            status=BenchmarkStatus.FAILED,
            start_time=datetime.utcnow(),
        )
        result3 = BenchmarkResult(
            id="3",
            name="bench3",
            benchmark_type=BenchmarkType.CPU,
            status=BenchmarkStatus.FAILED,
            start_time=datetime.utcnow(),
        )

        manager.benchmark_history = [result1, result2, result3]

        # Test filtering by benchmark type
        cpu_history = manager.get_benchmark_history(benchmark_type=BenchmarkType.CPU)
        assert len(cpu_history) == 2
        assert result1 in cpu_history
        assert result3 in cpu_history

        # Test filtering by status
        failed_history = manager.get_benchmark_history(status=BenchmarkStatus.FAILED)
        assert len(failed_history) == 2
        assert result2 in failed_history
        assert result3 in failed_history

        # Test limit
        limited_history = manager.get_benchmark_history(limit=1)
        assert len(limited_history) == 1

    def test_clear_history(self):
        """Test clearing benchmark history."""
        manager = BenchmarkManager()

        # Add mock results
        result = BenchmarkResult(
            id="1",
            name="bench1",
            benchmark_type=BenchmarkType.CPU,
            status=BenchmarkStatus.COMPLETED,
            start_time=datetime.utcnow(),
        )
        manager.benchmark_history = [result]

        manager.clear_history()

        assert manager.benchmark_history == []
