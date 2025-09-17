"""
Performance Baseline Tests
Establishes and monitors performance baselines for critical operations.
"""

import asyncio
import json
import time
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any, Callable, Dict, List, Optional

import pytest
from dotmac.platform.auth.jwt_service import JWTService
from dotmac.platform.auth.rbac_engine import RBACEngine, Role, Permission
from dotmac.platform.auth.session_manager import MemorySessionBackend, SessionManager, SessionConfig


@dataclass
class PerformanceMetrics:
    """Performance metrics for an operation"""

    operation: str
    samples: List[float]
    unit: str = "ms"

    @property
    def min_time(self) -> float:
        return min(self.samples) if self.samples else 0

    @property
    def max_time(self) -> float:
        return max(self.samples) if self.samples else 0

    @property
    def mean_time(self) -> float:
        return mean(self.samples) if self.samples else 0

    @property
    def median_time(self) -> float:
        return median(self.samples) if self.samples else 0

    @property
    def std_dev(self) -> float:
        return stdev(self.samples) if len(self.samples) > 1 else 0

    @property
    def p95(self) -> float:
        """95th percentile"""
        if not self.samples:
            return 0
        sorted_samples = sorted(self.samples)
        index = int(len(sorted_samples) * 0.95)
        return sorted_samples[min(index, len(sorted_samples) - 1)]

    @property
    def p99(self) -> float:
        """99th percentile"""
        if not self.samples:
            return 0
        sorted_samples = sorted(self.samples)
        index = int(len(sorted_samples) * 0.99)
        return sorted_samples[min(index, len(sorted_samples) - 1)]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting"""
        return {
            "operation": self.operation,
            "samples": len(self.samples),
            "unit": self.unit,
            "min": round(self.min_time, 3),
            "max": round(self.max_time, 3),
            "mean": round(self.mean_time, 3),
            "median": round(self.median_time, 3),
            "std_dev": round(self.std_dev, 3),
            "p95": round(self.p95, 3),
            "p99": round(self.p99, 3),
        }


class PerformanceBaseline:
    """Manages performance baselines and regression detection"""

    def __init__(self, baseline_file: Optional[Path] = None):
        self.baseline_file = baseline_file or Path("performance_baseline.json")
        self.current_metrics: Dict[str, PerformanceMetrics] = {}
        self.baseline_metrics: Dict[str, Dict[str, float]] = {}

        if self.baseline_file.exists():
            self.load_baseline()

    def load_baseline(self) -> None:
        """Load baseline metrics from file"""
        with open(self.baseline_file) as f:
            self.baseline_metrics = json.load(f)

    def save_baseline(self) -> None:
        """Save current metrics as new baseline"""
        baseline_data = {name: metrics.to_dict() for name, metrics in self.current_metrics.items()}
        with open(self.baseline_file, "w") as f:
            json.dump(baseline_data, f, indent=2)

    def measure(
        self,
        operation: str,
        func: Callable,
        *args,
        iterations: int = 100,
        warmup: int = 10,
        **kwargs,
    ) -> PerformanceMetrics:
        """Measure performance of a synchronous operation"""
        # Warmup
        for _ in range(warmup):
            func(*args, **kwargs)

        # Measure
        samples = []
        for _ in range(iterations):
            start = time.perf_counter()
            func(*args, **kwargs)
            end = time.perf_counter()
            samples.append((end - start) * 1000)  # Convert to ms

        metrics = PerformanceMetrics(operation, samples)
        self.current_metrics[operation] = metrics
        return metrics

    async def measure_async(
        self,
        operation: str,
        func: Callable,
        *args,
        iterations: int = 100,
        warmup: int = 10,
        **kwargs,
    ) -> PerformanceMetrics:
        """Measure performance of an async operation"""
        # Warmup
        for _ in range(warmup):
            await func(*args, **kwargs)

        # Measure
        samples = []
        for _ in range(iterations):
            start = time.perf_counter()
            await func(*args, **kwargs)
            end = time.perf_counter()
            samples.append((end - start) * 1000)  # Convert to ms

        metrics = PerformanceMetrics(operation, samples)
        self.current_metrics[operation] = metrics
        return metrics

    def check_regression(self, operation: str, threshold_percent: float = 20.0) -> Optional[str]:
        """Check if performance has regressed compared to baseline"""
        if operation not in self.current_metrics:
            return None

        if operation not in self.baseline_metrics:
            return None  # No baseline to compare

        current = self.current_metrics[operation]
        baseline = self.baseline_metrics[operation]

        # Compare p95 values
        baseline_p95 = baseline.get("p95", 0)
        current_p95 = current.p95

        if baseline_p95 > 0:
            percent_change = ((current_p95 - baseline_p95) / baseline_p95) * 100

            if percent_change > threshold_percent:
                return (
                    f"Performance regression detected for {operation}: "
                    f"p95 increased by {percent_change:.1f}% "
                    f"(baseline: {baseline_p95:.3f}ms, current: {current_p95:.3f}ms)"
                )

        return None

    def generate_report(self) -> str:
        """Generate performance report"""
        report = ["Performance Test Report", "=" * 50, ""]

        for operation, metrics in self.current_metrics.items():
            report.append(f"Operation: {operation}")
            report.append("-" * 30)

            data = metrics.to_dict()
            for key, value in data.items():
                if key not in ["operation", "samples", "unit"]:
                    report.append(f"  {key:10s}: {value:8.3f} {metrics.unit}")

            # Check for regression
            regression = self.check_regression(operation)
            if regression:
                report.append(f"  ⚠️  {regression}")

            report.append("")

        return "\n".join(report)


@pytest.mark.slow
@pytest.mark.benchmark
class TestJWTPerformance:
    """Performance tests for JWT operations"""

    @pytest.fixture
    def jwt_service(self):
        return JWTService(
            algorithm="HS256",
            secret="test-secret-key-for-performance",
            issuer="perf-test",
            default_audience="perf-test",
        )

    @pytest.fixture
    def baseline(self):
        return PerformanceBaseline(Path("jwt_performance_baseline.json"))

    def test_jwt_token_generation_performance(self, jwt_service, baseline):
        """Benchmark JWT token generation"""

        def generate_token():
            return jwt_service.issue_access_token(
                "user123",
                tenant_id="tenant456",
                extra_claims={"role": "admin", "permissions": ["read", "write"]},
            )

        metrics = baseline.measure(
            "jwt_token_generation", generate_token, iterations=1000, warmup=100
        )

        # Assert performance requirements
        assert metrics.median_time < 5.0, f"JWT generation too slow: {metrics.median_time:.3f}ms"
        assert metrics.p95 < 10.0, f"JWT generation p95 too slow: {metrics.p95:.3f}ms"

        # Check for regression
        regression = baseline.check_regression("jwt_token_generation")
        if regression:
            pytest.warning(regression)

    def test_jwt_token_verification_performance(self, jwt_service, baseline):
        """Benchmark JWT token verification"""
        # Pre-generate tokens
        tokens = [jwt_service.issue_access_token(f"user{i}") for i in range(100)]

        token_index = 0

        def verify_token():
            nonlocal token_index
            jwt_service.verify_token(tokens[token_index % len(tokens)])
            token_index += 1

        metrics = baseline.measure(
            "jwt_token_verification", verify_token, iterations=1000, warmup=100
        )

        # Assert performance requirements
        assert metrics.median_time < 3.0, f"JWT verification too slow: {metrics.median_time:.3f}ms"
        assert metrics.p95 < 8.0, f"JWT verification p95 too slow: {metrics.p95:.3f}ms"


@pytest.mark.slow
@pytest.mark.benchmark
class TestRBACPerformance:
    """Performance tests for RBAC operations"""

    @pytest.fixture
    def rbac_engine(self):
        engine = RBACEngine()

        # Create test roles and permissions
        for i in range(10):
            role = Role(f"role_{i}", f"Test Role {i}")
            for j in range(20):
                perm = Permission(f"resource_{j}", f"action_{i}")
                role.add_permission(perm)
            engine.add_role(role)

        return engine

    @pytest.fixture
    def baseline(self):
        return PerformanceBaseline(Path("rbac_performance_baseline.json"))

    def test_permission_check_performance(self, rbac_engine, baseline):
        """Benchmark permission checking"""

        # Assign roles to user
        user_roles = ["role_0", "role_1", "role_2"]

        def check_permission():
            return rbac_engine.check_permission(user_roles, "resource_5", "action_1")

        metrics = baseline.measure(
            "rbac_permission_check", check_permission, iterations=10000, warmup=1000
        )

        # Assert performance requirements
        assert metrics.median_time < 0.5, f"Permission check too slow: {metrics.median_time:.3f}ms"
        assert metrics.p95 < 1.0, f"Permission check p95 too slow: {metrics.p95:.3f}ms"

    def test_role_assignment_performance(self, rbac_engine, baseline):
        """Benchmark role assignment"""

        user_index = 0

        def assign_role():
            nonlocal user_index
            user_id = f"user_{user_index}"
            rbac_engine.assign_role_to_user(user_id, "role_0")
            user_index += 1

        metrics = baseline.measure("rbac_role_assignment", assign_role, iterations=1000, warmup=100)

        # Assert performance requirements
        assert metrics.median_time < 1.0, f"Role assignment too slow: {metrics.median_time:.3f}ms"
        assert metrics.p95 < 2.0, f"Role assignment p95 too slow: {metrics.p95:.3f}ms"


@pytest.mark.slow
@pytest.mark.benchmark
class TestSessionPerformance:
    """Performance tests for session management"""

    @pytest.fixture
    def session_manager(self):
        config = SessionConfig(session_lifetime_seconds=3600, max_sessions_per_user=10)
        backend = MemorySessionBackend()
        return SessionManager(config=config, backend=backend)

    @pytest.fixture
    def baseline(self):
        return PerformanceBaseline(Path("session_performance_baseline.json"))

    @pytest.mark.asyncio
    async def test_session_creation_performance(self, session_manager, baseline):
        """Benchmark session creation"""

        user_index = 0

        async def create_session():
            nonlocal user_index
            session = await session_manager.create_session(
                user_id=f"user_{user_index}", metadata={"ip": "192.168.1.1", "user_agent": "test"}
            )
            user_index += 1
            return session

        metrics = await baseline.measure_async(
            "session_creation", create_session, iterations=1000, warmup=100
        )

        # Assert performance requirements
        assert metrics.median_time < 2.0, f"Session creation too slow: {metrics.median_time:.3f}ms"
        assert metrics.p95 < 5.0, f"Session creation p95 too slow: {metrics.p95:.3f}ms"

    @pytest.mark.asyncio
    async def test_session_validation_performance(self, session_manager, baseline):
        """Benchmark session validation"""

        # Pre-create sessions
        sessions = []
        for i in range(100):
            session = await session_manager.create_session(user_id=f"user_{i}", metadata={})
            sessions.append(session.session_id)

        session_index = 0

        async def validate_session():
            nonlocal session_index
            session_id = sessions[session_index % len(sessions)]
            result = await session_manager.validate_session(session_id)
            session_index += 1
            return result

        metrics = await baseline.measure_async(
            "session_validation", validate_session, iterations=10000, warmup=1000
        )

        # Assert performance requirements
        assert (
            metrics.median_time < 0.5
        ), f"Session validation too slow: {metrics.median_time:.3f}ms"
        assert metrics.p95 < 1.0, f"Session validation p95 too slow: {metrics.p95:.3f}ms"


@pytest.mark.slow
@pytest.mark.benchmark
class TestEndToEndPerformance:
    """End-to-end performance tests"""

    @pytest.fixture
    def services(self):
        """Setup all services for end-to-end testing"""
        return {
            "jwt": JWTService(
                algorithm="HS256", secret="test-secret", issuer="test", default_audience="test"
            ),
            "rbac": RBACEngine(),
            "session": SessionManager(config=SessionConfig(), backend=MemorySessionBackend()),
        }

    @pytest.fixture
    def baseline(self):
        return PerformanceBaseline(Path("e2e_performance_baseline.json"))

    @pytest.mark.asyncio
    async def test_full_auth_flow_performance(self, services, baseline):
        """Benchmark complete authentication flow"""

        # Setup RBAC
        admin_role = Role("admin", "Administrator")
        admin_role.add_permission(Permission("*", "*"))
        services["rbac"].add_role(admin_role)

        user_index = 0

        async def full_auth_flow():
            nonlocal user_index
            user_id = f"user_{user_index}"

            # 1. Generate JWT token
            token = services["jwt"].issue_access_token(user_id, extra_claims={"roles": ["admin"]})

            # 2. Verify token
            claims = services["jwt"].verify_token(token)

            # 3. Check permissions
            has_perm = services["rbac"].check_permission(["admin"], "users", "read")

            # 4. Create session
            session = await services["session"].create_session(
                user_id=user_id, metadata={"token_jti": claims.get("jti")}
            )

            # 5. Validate session
            valid = await services["session"].validate_session(session.session_id)

            user_index += 1
            return valid

        metrics = await baseline.measure_async(
            "full_auth_flow", full_auth_flow, iterations=500, warmup=50
        )

        # Assert end-to-end performance requirements
        assert metrics.median_time < 10.0, f"Full auth flow too slow: {metrics.median_time:.3f}ms"
        assert metrics.p95 < 20.0, f"Full auth flow p95 too slow: {metrics.p95:.3f}ms"

        # Generate report
        report = baseline.generate_report()
        print("\n" + report)

        # Optionally save as new baseline
        # baseline.save_baseline()


@pytest.mark.slow
@pytest.mark.benchmark
class TestConcurrentPerformance:
    """Test performance under concurrent load"""

    @pytest.mark.asyncio
    async def test_concurrent_jwt_operations(self):
        """Test JWT service under concurrent load"""
        jwt_service = JWTService(
            algorithm="HS256", secret="test-secret", issuer="test", default_audience="test"
        )

        async def jwt_operation(index: int):
            # Generate token
            token = jwt_service.issue_access_token(f"user_{index}")
            # Verify token
            claims = jwt_service.verify_token(token)
            return claims["sub"] == f"user_{index}"

        # Run concurrent operations
        start = time.perf_counter()
        tasks = [jwt_operation(i) for i in range(1000)]
        results = await asyncio.gather(*tasks)
        end = time.perf_counter()

        # All should succeed
        assert all(results)

        # Calculate throughput
        duration = end - start
        throughput = len(tasks) / duration

        print(f"\nJWT Operations: {len(tasks)} operations in {duration:.2f}s")
        print(f"Throughput: {throughput:.0f} ops/sec")

        # Assert minimum throughput
        assert throughput > 100, f"JWT throughput too low: {throughput:.0f} ops/sec"

    @pytest.mark.skip(reason="Concurrent performance test removed")
    @pytest.mark.asyncio
    async def test_concurrent_session_operations(self):
        """Test session manager under concurrent load"""
        session_manager = SessionManager(
            config=SessionConfig(max_sessions_per_user=100), backend=MemorySessionBackend()
        )

        async def session_operation(index: int):
            user_id = f"user_{index % 10}"  # 10 unique users
            # Create session
            session = await session_manager.create_session(
                user_id=user_id, metadata={"request_id": index}
            )
            # Validate session
            valid = await session_manager.validate_session(session.session_id)
            # Clean up
            await session_manager.terminate_session(session.session_id)
            return valid is not None

        # Run concurrent operations
        start = time.perf_counter()
        tasks = [session_operation(i) for i in range(500)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end = time.perf_counter()

        # Count successes
        successes = sum(1 for r in results if r is True)
        failures = len(results) - successes

        # Calculate throughput
        duration = end - start
        throughput = len(tasks) / duration

        print(f"\nSession Operations: {len(tasks)} operations in {duration:.2f}s")
        print(f"Success: {successes}, Failures: {failures}")
        print(f"Throughput: {throughput:.0f} ops/sec")

        # Most should succeed
        assert successes > len(tasks) * 0.95
        assert throughput > 50, f"Session throughput too low: {throughput:.0f} ops/sec"
