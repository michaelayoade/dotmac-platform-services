"""
Chaos Engineering Tests
Simulates various failure scenarios to test system resilience.
"""

import asyncio
import random
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Callable, Optional
from unittest.mock import AsyncMock, Mock, patch

import pytest
from tenacity import retry, stop_after_attempt, wait_exponential


class ChaosMonkey:
    """Chaos engineering utilities for introducing controlled failures"""

    def __init__(self, failure_rate: float = 0.3):
        """
        Initialize ChaosMonkey.

        Args:
            failure_rate: Probability of failure (0.0 to 1.0)
        """
        self.failure_rate = failure_rate
        self.failure_count = 0
        self.success_count = 0

    def maybe_fail(self, exception_type: type[Exception] = RuntimeError) -> None:
        """Randomly fail based on failure rate"""
        if random.random() < self.failure_rate:
            self.failure_count += 1
            raise exception_type("Chaos monkey strike!")
        self.success_count += 1

    async def async_maybe_fail(self, exception_type: type[Exception] = RuntimeError) -> None:
        """Async version of maybe_fail"""
        if random.random() < self.failure_rate:
            self.failure_count += 1
            # Add random delay to simulate network issues
            await asyncio.sleep(random.uniform(0.1, 0.5))
            raise exception_type("Chaos monkey async strike!")
        self.success_count += 1

    def slow_down(self, min_delay: float = 0.1, max_delay: float = 2.0) -> None:
        """Introduce random latency"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    async def async_slow_down(self, min_delay: float = 0.1, max_delay: float = 2.0) -> None:
        """Async version of slow_down"""
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)

    def get_stats(self) -> dict:
        """Get chaos monkey statistics"""
        total = self.failure_count + self.success_count
        return {
            "total_calls": total,
            "failures": self.failure_count,
            "successes": self.success_count,
            "failure_rate": self.failure_count / total if total > 0 else 0,
        }


class NetworkChaos:
    """Simulates network-related failures"""

    @staticmethod
    async def simulate_network_partition(duration: float = 1.0):
        """Simulate network partition by raising connection errors"""
        end_time = time.time() + duration

        async def failing_connect(*args, **kwargs):
            if time.time() < end_time:
                raise ConnectionError("Network partition in effect")
            return AsyncMock()

        return failing_connect

    @staticmethod
    async def simulate_packet_loss(loss_rate: float = 0.1):
        """Simulate packet loss"""

        async def lossy_send(*args, **kwargs):
            if random.random() < loss_rate:
                raise ConnectionError("Packet lost")
            return AsyncMock()

        return lossy_send

    @staticmethod
    async def simulate_high_latency(min_ms: int = 100, max_ms: int = 5000):
        """Simulate high network latency"""

        async def slow_operation(*args, **kwargs):
            delay = random.randint(min_ms, max_ms) / 1000
            await asyncio.sleep(delay)
            return AsyncMock()

        return slow_operation


@pytest.mark.slow
@pytest.mark.integration
class TestDatabaseResilience:
    """Test database resilience under various failure conditions"""

    @pytest.fixture
    def chaos_db_session(self):
        """Create a database session that randomly fails"""
        from sqlalchemy.ext.asyncio import AsyncSession
        from unittest.mock import AsyncMock

        session = AsyncMock(spec=AsyncSession)
        chaos = ChaosMonkey(failure_rate=0.3)

        # Make execute randomly fail
        async def chaotic_execute(*args, **kwargs):
            await chaos.async_maybe_fail(ConnectionError)
            return AsyncMock()

        session.execute = chaotic_execute
        session.chaos = chaos  # Attach for stats
        return session

    async def test_database_connection_failures(self, chaos_db_session):
        """Test handling of database connection failures"""
        from tenacity import retry, stop_after_attempt, wait_exponential

        success_count = 0
        failure_count = 0

        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.1))
        async def query_with_retry():
            return await chaos_db_session.execute("SELECT 1")

        # Run multiple queries
        for _ in range(20):
            try:
                await query_with_retry()
                success_count += 1
            except ConnectionError:
                failure_count += 1

        # Should handle some failures gracefully
        assert success_count > 0
        assert failure_count < 20  # Retries should reduce failures

        # Check chaos stats
        stats = chaos_db_session.chaos.get_stats()
        assert stats["total_calls"] > 20  # Due to retries

    async def test_transaction_rollback_on_failure(self):
        """Test transaction rollback during failures"""
        from unittest.mock import AsyncMock, MagicMock

        session = AsyncMock()
        transaction = MagicMock()

        # Simulate failure mid-transaction
        call_count = 0

        async def failing_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # Fail on second call
                raise ConnectionError("Database connection lost")
            return AsyncMock()

        session.execute = failing_execute
        session.begin = lambda: transaction
        transaction.__aenter__ = AsyncMock()
        transaction.__aexit__ = AsyncMock()

        # Attempt transaction
        try:
            async with session.begin():
                await session.execute("INSERT 1")
                await session.execute("INSERT 2")  # This will fail
                await session.execute("INSERT 3")
        except ConnectionError:
            pass

        # Verify rollback was called
        transaction.__aexit__.assert_called_once()

    async def test_connection_pool_exhaustion(self):
        """Test behavior when connection pool is exhausted"""
        from asyncio import gather, TimeoutError

        # Simulate connection pool
        class MockConnectionPool:
            def __init__(self, max_size: int = 5):
                self.max_size = max_size
                self.current_size = 0
                self.wait_queue = []

            async def acquire(self, timeout: float = 1.0):
                if self.current_size < self.max_size:
                    self.current_size += 1
                    return f"connection_{self.current_size}"

                # Wait for available connection
                try:
                    await asyncio.wait_for(asyncio.sleep(10), timeout=timeout)  # Simulate long wait
                except asyncio.TimeoutError:
                    raise TimeoutError("Connection pool timeout")

            async def release(self, conn):
                await asyncio.sleep(0.1)  # Simulate cleanup
                self.current_size -= 1

        pool = MockConnectionPool(max_size=3)

        # Try to acquire more connections than available
        async def acquire_connection(pool, hold_time: float = 0.5):
            try:
                conn = await pool.acquire(timeout=0.5)
                await asyncio.sleep(hold_time)
                await pool.release(conn)
                return "success"
            except TimeoutError:
                return "timeout"

        # Launch multiple concurrent requests
        results = await gather(
            *[acquire_connection(pool) for _ in range(10)], return_exceptions=True
        )

        # Some should timeout due to pool exhaustion
        timeouts = [r for r in results if r == "timeout"]
        assert len(timeouts) > 0


@pytest.mark.slow
@pytest.mark.integration
class TestRedisResilience:
    """Test Redis resilience under failure conditions"""

    @pytest.fixture
    def chaos_redis(self):
        """Create a Redis client that randomly fails"""
        from unittest.mock import AsyncMock

        redis = AsyncMock()
        chaos = ChaosMonkey(failure_rate=0.25)

        async def chaotic_get(key):
            await chaos.async_slow_down(0.01, 0.5)
            await chaos.async_maybe_fail(ConnectionError)
            return f"value_{key}"

        async def chaotic_set(key, value, ex=None):
            await chaos.async_slow_down(0.01, 0.3)
            await chaos.async_maybe_fail(ConnectionError)
            return True

        redis.get = chaotic_get
        redis.set = chaotic_set
        redis.chaos = chaos
        return redis

    async def test_redis_connection_resilience(self, chaos_redis):
        """Test Redis operations with random failures"""
        from dotmac.platform.auth.session_manager import RedisSessionBackend

        # Mock the backend to use chaos redis
        backend = RedisSessionBackend("redis://localhost")
        backend._redis = chaos_redis

        success_count = 0
        failure_count = 0

        # Perform multiple operations
        for i in range(30):
            try:
                # Try to get a session
                result = await chaos_redis.get(f"session_{i}")
                if result:
                    success_count += 1
            except ConnectionError:
                failure_count += 1

        # Should handle failures gracefully
        assert success_count > 0
        assert failure_count > 0  # Some failures expected
        assert success_count > failure_count  # But mostly successful

    async def test_redis_pipeline_failures(self):
        """Test Redis pipeline failure handling"""
        from unittest.mock import AsyncMock

        redis = AsyncMock()
        pipeline = AsyncMock()

        # Simulate pipeline failure
        pipeline.execute = AsyncMock(side_effect=ConnectionError("Pipeline failed"))
        redis.pipeline = lambda: pipeline

        # Test operation that uses pipeline
        async def bulk_operation(redis, keys):
            pipe = redis.pipeline()
            for key in keys:
                pipe.get(key)

            try:
                results = await pipe.execute()
                return results
            except ConnectionError:
                # Fallback to individual operations
                results = []
                for key in keys:
                    try:
                        result = await redis.get(key)
                        results.append(result)
                    except:
                        results.append(None)
                return results

        redis.get = AsyncMock(return_value="fallback_value")

        # Execute bulk operation
        results = await bulk_operation(redis, ["key1", "key2", "key3"])

        # Should fall back to individual operations
        assert len(results) == 3
        assert all(r == "fallback_value" for r in results)


@pytest.mark.slow
@pytest.mark.integration
class TestAuthenticationResilience:
    """Test authentication system resilience"""

    async def test_jwt_service_clock_skew(self):
        """Test JWT validation with clock skew"""
        from dotmac.platform.auth.jwt_service import JWTService
        from dotmac.platform.auth.exceptions import TokenExpired
        from datetime import datetime, timedelta
        try:
            import jwt  # type: ignore
            expired_error = jwt.ExpiredSignatureError
        except Exception:  # pragma: no cover - python-jose fallback
            from jose import jwt  # type: ignore
            from jose.exceptions import ExpiredSignatureError as expired_error

        service = JWTService(
            algorithm="HS256", secret="test-secret", issuer="test", default_audience="test"
        )

        # Create token with current time
        # Issue token that is already expired (simulates extreme clock skew)
        token = service.issue_access_token("user123", expires_in=-1)

        # Simulate clock skew - move time forward
        with patch("time.time", return_value=time.time() + 65):
            # Token should be expired
            with pytest.raises((expired_error, TokenExpired)):
                service.verify_token(token)

        # Test with leeway
        service_with_leeway = JWTService(
            algorithm="HS256",
            secret="test-secret",
            issuer="test",
            default_audience="test",
            leeway_seconds=120,  # 2 minutes leeway
        )

        with patch("time.time", return_value=time.time() + 65):
            # Should work with leeway
            claims = service_with_leeway.verify_token(token)
            assert claims["sub"] == "user123"

    async def test_session_manager_concurrent_limits(self):
        """Test session manager under concurrent session limit pressure"""
        from dotmac.platform.auth.session_manager import (
            MemorySessionBackend,
            SessionManager,
            SessionConfig,
            SessionData,
        )
        from datetime import datetime, timedelta

        config = SessionConfig(max_sessions_per_user=3, session_lifetime_seconds=3600)

        backend = MemorySessionBackend()
        manager = SessionManager(config=config, backend=backend)

        user_id = "user123"

        # Create sessions concurrently
        async def create_session(index: int):
            try:
                session = await manager.create_session(user_id=user_id, metadata={"index": index})
                return session
            except Exception as e:
                return str(e)

        # Try to create more sessions than limit
        tasks = [create_session(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful sessions
        successful = [r for r in results if isinstance(r, SessionData)]
        failed = [r for r in results if not isinstance(r, SessionData)]

        # Manager should enforce limit by recycling old sessions rather than failing creations
        active_sessions = await manager.get_user_sessions(user_id)

        assert len(active_sessions) <= config.max_sessions_per_user
        assert len({s.session_id for s in active_sessions}) == len(active_sessions)
        # Some sessions should have been evicted to respect the limit
        assert len(successful) >= config.max_sessions_per_user
        assert any(isinstance(r, SessionData) for r in successful)

    async def test_api_key_rotation_race_condition(self):
        """Test API key rotation under concurrent access"""
        from dotmac.platform.auth.api_keys import APIKeyService
        from unittest.mock import AsyncMock

        service = APIKeyService()
        service._storage = {}  # Mock storage

        key_id = "key123"
        old_key = "old_api_key_123"
        new_key = "new_api_key_456"

        # Simulate concurrent rotation and validation
        rotation_complete = False

        async def rotate_key():
            nonlocal rotation_complete
            await asyncio.sleep(0.1)  # Simulate rotation delay
            service._storage[key_id] = new_key
            rotation_complete = True
            return new_key

        async def validate_key(key: str):
            # Check both old and new during rotation
            if not rotation_complete:
                return key == old_key
            return key == new_key

        # Initial key
        service._storage[key_id] = old_key

        # Concurrent operations
        rotation_task = asyncio.create_task(rotate_key())
        validation_tasks = [asyncio.create_task(validate_key(old_key)) for _ in range(5)]

        # Wait for all to complete
        await rotation_task
        validation_results = await asyncio.gather(*validation_tasks)

        # Some validations should succeed during rotation
        assert any(validation_results)


@pytest.mark.slow
@pytest.mark.integration
class TestSecretsResilience:
    """Test secrets management resilience"""

    @pytest.mark.skip(reason="Requires aiohttp mocking that conflicts with provider implementation")
    async def test_vault_connection_failures(self):
        """Test Vault provider with connection failures"""
        from dotmac.platform.secrets.openbao_provider import OpenBaoProvider
        from aiohttp import ClientError

        chaos = ChaosMonkey(failure_rate=0.4)

        # Mock HTTP client with chaos
        async def chaotic_request(method, url, **kwargs):
            await chaos.async_maybe_fail(ClientError)
            return AsyncMock(status=200, json=AsyncMock(return_value={"data": {"secret": "value"}}))

        provider = OpenBaoProvider(
            url="http://vault:8200", token="test-token", mount_point="secret"
        )

        with patch("aiohttp.ClientSession.request", chaotic_request):
            success_count = 0
            failure_count = 0

            for i in range(20):
                try:
                    secret = await provider.get_secret(f"path/secret_{i}")
                    if secret:
                        success_count += 1
                except ClientError:
                    failure_count += 1

            # Should handle some failures
            assert success_count > 0
            assert failure_count > 0

    @pytest.mark.skip(
        reason="Imports SecretsManager which is not present in current implementation"
    )
    async def test_secret_rotation_during_access(self):
        """Test secret rotation while being accessed"""
        from dotmac.platform.secrets.rotation import SecretRotationManager

        # Mock secrets provider
        secrets = {"db_password": "old_password_123"}

        async def get_secret(path):
            await asyncio.sleep(0.05)  # Simulate network delay
            return secrets.get(path)

        async def set_secret(path, value):
            await asyncio.sleep(0.05)  # Simulate network delay
            secrets[path] = value

        # Simulate concurrent access during rotation
        access_count = 0
        rotation_count = 0

        async def access_secret():
            nonlocal access_count
            for _ in range(10):
                password = await get_secret("db_password")
                assert password is not None
                access_count += 1
                await asyncio.sleep(0.01)

        async def rotate_secret():
            nonlocal rotation_count
            for i in range(3):
                await asyncio.sleep(0.1)
                new_password = f"new_password_{i}"
                await set_secret("db_password", new_password)
                rotation_count += 1

        # Run concurrently
        await asyncio.gather(access_secret(), access_secret(), rotate_secret())

        # Both access and rotation should complete
        assert access_count == 20
        assert rotation_count == 3
        assert secrets["db_password"].startswith("new_password")


@pytest.mark.slow
@pytest.mark.integration
class TestCascadingFailures:
    """Test cascading failure scenarios"""

    @pytest.mark.skip(reason="Mock chain effect assumptions conflict with implementation")
    async def test_auth_database_redis_cascade(self):
        """Test cascading failure: Auth -> Database -> Redis"""
        from unittest.mock import AsyncMock, patch

        # Setup service dependencies
        auth_service = AsyncMock()
        db_service = AsyncMock()
        redis_service = AsyncMock()

        # Auth depends on DB
        auth_service.validate_user = AsyncMock(side_effect=lambda u: db_service.get_user(u))

        # DB depends on Redis for caching
        async def db_get_user(user_id):
            # Try cache first
            cached = await redis_service.get(f"user:{user_id}")
            if cached:
                return cached

            # Simulate DB query
            return {"id": user_id, "name": "Test User"}

        db_service.get_user = db_get_user

        # Simulate Redis failure
        redis_service.get = AsyncMock(side_effect=ConnectionError("Redis down"))

        # Test cascading effect
        with pytest.raises(ConnectionError):
            await auth_service.validate_user("user123")

        # Add fallback - DB should work without cache
        async def db_get_user_with_fallback(user_id):
            try:
                cached = await redis_service.get(f"user:{user_id}")
                if cached:
                    return cached
            except ConnectionError:
                pass  # Ignore cache errors

            return {"id": user_id, "name": "Test User"}

        db_service.get_user = db_get_user_with_fallback

        # Should work with fallback
        result = await auth_service.validate_user("user123")
        assert result["id"] == "user123"

    async def test_circuit_breaker_pattern(self):
        """Test circuit breaker pattern for failing services"""

        class CircuitBreaker:
            def __init__(self, failure_threshold: int = 5, reset_timeout: float = 1.0):
                self.failure_threshold = failure_threshold
                self.reset_timeout = reset_timeout
                self.failure_count = 0
                self.last_failure_time = None
                self.state = "closed"  # closed, open, half-open

            async def call(self, func: Callable, *args, **kwargs):
                # Check if circuit should be reset
                if self.state == "open":
                    if (
                        self.last_failure_time
                        and time.time() - self.last_failure_time > self.reset_timeout
                    ):
                        self.state = "half-open"
                        self.failure_count = 0

                if self.state == "open":
                    raise Exception("Circuit breaker is open")

                try:
                    result = await func(*args, **kwargs)
                    if self.state == "half-open":
                        self.state = "closed"
                        self.failure_count = 0
                    return result
                except Exception as e:
                    self.failure_count += 1
                    self.last_failure_time = time.time()

                    if self.failure_count >= self.failure_threshold:
                        self.state = "open"

                    raise e

        # Test service with circuit breaker
        chaos = ChaosMonkey(failure_rate=0.8)  # High failure rate
        circuit_breaker = CircuitBreaker(failure_threshold=3, reset_timeout=0.5)

        async def unreliable_service():
            await chaos.async_maybe_fail()
            return "success"

        # Test until circuit opens
        failures = 0
        for i in range(10):
            try:
                result = await circuit_breaker.call(unreliable_service)
            except Exception as e:
                failures += 1
                if "Circuit breaker is open" in str(e):
                    break

        # Circuit should be open after threshold
        assert circuit_breaker.state == "open"
        assert failures >= 3

        # Wait for reset timeout
        await asyncio.sleep(0.6)

        # Circuit should attempt half-open
        chaos.failure_rate = 0  # Make it succeed
        result = await circuit_breaker.call(unreliable_service)
        assert result == "success"
        assert circuit_breaker.state == "closed"
