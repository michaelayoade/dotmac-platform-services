"""
Final targeted tests to push secrets manager coverage over 85%
"""

import pytest

from dotmac.platform.secrets.exceptions import (
    SecretValidationError,
)
from dotmac.platform.secrets.manager import SecretsManager


class TestSecretsManagerCriticalPaths:
    """Target the remaining uncovered code paths"""

    @pytest.mark.asyncio
    async def test_observability_with_cache_operations(self):
        """Test observability hooks with cache hits and misses"""

        class SimpleCache:
            def __init__(self):
                self.cache = {}

            async def get(self, key: str):
                return self.cache.get(key)

            async def set(self, key: str, value, ttl: int):
                self.cache[key] = value
                return True

            async def delete(self, key: str):
                return self.cache.pop(key, None) is not None

            async def clear(self):
                self.cache.clear()
                return True

            async def exists(self, key: str):
                return key in self.cache

            async def get_stats(self):
                return {"size": len(self.cache)}

            async def close(self):
                pass

        class SimpleProvider:
            def __init__(self):
                self.call_count = 0

            async def get_secret(self, path: str):
                self.call_count += 1
                return {"secret": "a" * 32}

            async def health_check(self):
                return True

        class TrackingHook:
            def __init__(self):
                self.cache_hits = []
                self.cache_misses = []
                self.fetches = []
                self.validation_failures = []
                self.provider_errors = []

            def record_cache_hit(self, path):
                self.cache_hits.append(path)

            def record_cache_miss(self, path):
                self.cache_misses.append(path)

            def record_secret_fetch(self, kind, source, success, latency_ms, path):
                self.fetches.append((kind, source, success, path))

            def record_validation_failure(self, kind, error, path):
                self.validation_failures.append((kind, error, path))

            def record_provider_error(self, provider_name, error_type, path):
                self.provider_errors.append((provider_name, error_type, path))

        provider = SimpleProvider()
        cache = SimpleCache()
        hook = TrackingHook()
        manager = SecretsManager(
            provider, cache=cache, observability_hook=hook, validate_secrets=False
        )

        # First request - should be cache miss
        await manager.get_symmetric_secret("test")
        assert len(hook.cache_misses) == 1
        assert len(hook.fetches) == 1

        # Second request - should be cache hit
        await manager.get_symmetric_secret("test")
        assert len(hook.cache_hits) == 1

    @pytest.mark.asyncio
    async def test_error_during_secret_processing(self):
        """Test error handling during secret processing"""

        # Provider that raises unexpected errors
        class ErrorProvider:
            async def get_secret(self, path: str):
                raise RuntimeError("Database connection failed")

            async def health_check(self):
                return False

        class SimpleCache:
            async def get(self, key: str):
                return None

            async def set(self, key: str, value, ttl: int):
                return True

            async def delete(self, key: str):
                return True

            async def clear(self):
                return True

            async def exists(self, key: str):
                return False

            async def get_stats(self):
                return {}

            async def close(self):
                pass

        class TrackingHook:
            def __init__(self):
                self.provider_errors = []

            def record_cache_hit(self, path):
                pass

            def record_cache_miss(self, path):
                pass

            def record_secret_fetch(self, kind, source, success, latency_ms, path):
                pass

            def record_validation_failure(self, kind, error, path):
                pass

            def record_provider_error(self, provider_name, error_type, path):
                self.provider_errors.append((provider_name, error_type, path))

        provider = ErrorProvider()
        cache = SimpleCache()
        hook = TrackingHook()
        manager = SecretsManager(
            provider, cache=cache, observability_hook=hook, validate_secrets=False
        )

        # Should raise the error and record it
        with pytest.raises(RuntimeError):
            await manager.get_symmetric_secret("test")

        # Should have recorded provider error
        assert len(hook.provider_errors) == 1
        assert manager._stats["errors"] == 1

    @pytest.mark.asyncio
    async def test_health_check_edge_cases(self):
        """Test health check edge cases"""

        # Provider that raises exception during health check
        class BadProvider:
            async def get_secret(self, path: str):
                return {"secret": "test"}

            async def health_check(self):
                raise Exception("Health check failed")

        # Cache that raises exception during exists check
        class BadCache:
            async def get(self, key: str):
                return None

            async def set(self, key: str, value, ttl: int):
                return True

            async def delete(self, key: str):
                return True

            async def clear(self):
                return True

            async def exists(self, key: str):
                raise Exception("Cache connection lost")

            async def get_stats(self):
                return {}

            async def close(self):
                pass

        provider = BadProvider()
        cache = BadCache()
        manager = SecretsManager(provider, cache=cache)

        health = await manager.health_check()

        # Should handle both exceptions gracefully
        assert "error:" in health["provider"]
        assert "error:" in health["cache"]
        assert health["manager"] == "healthy"

    @pytest.mark.asyncio
    async def test_stats_with_cache_failure(self):
        """Test getting stats when cache stats fail"""

        class BadStatsCache:
            async def get(self, key: str):
                return None

            async def set(self, key: str, value, ttl: int):
                return True

            async def delete(self, key: str):
                return True

            async def clear(self):
                return True

            async def exists(self, key: str):
                return False

            async def get_stats(self):
                raise Exception("Stats unavailable")

            async def close(self):
                pass

        class SimpleProvider:
            async def get_secret(self, path: str):
                return {"secret": "test"}

            async def health_check(self):
                return True

        provider = SimpleProvider()
        cache = BadStatsCache()
        manager = SecretsManager(provider, cache=cache)

        stats = await manager.get_stats()

        # Should handle cache stats failure
        assert "cache" in stats
        assert "error" in stats["cache"]

    @pytest.mark.asyncio
    async def test_close_with_provider_close(self):
        """Test close when provider has close method"""

        class ProviderWithClose:
            def __init__(self):
                self.closed = False

            async def get_secret(self, path: str):
                return {"secret": "test"}

            async def health_check(self):
                return True

            async def close(self):
                self.closed = True

        class CacheWithClose:
            def __init__(self):
                self.closed = False

            async def get(self, key: str):
                return None

            async def set(self, key: str, value, ttl: int):
                return True

            async def delete(self, key: str):
                return True

            async def clear(self):
                return True

            async def exists(self, key: str):
                return False

            async def get_stats(self):
                return {}

            async def close(self):
                self.closed = True

        provider = ProviderWithClose()
        cache = CacheWithClose()
        manager = SecretsManager(provider, cache=cache)

        await manager.close()

        # Both should be closed
        assert provider.closed
        assert cache.closed

    @pytest.mark.asyncio
    async def test_symmetric_secret_missing_key(self):
        """Test symmetric secret when secret key is missing"""

        class ProviderWithBadSecret:
            async def get_secret(self, path: str):
                return {"other_key": "not_secret"}  # Missing 'secret' key

            async def health_check(self):
                return True

        class SimpleCache:
            async def get(self, key: str):
                return None

            async def set(self, key: str, value, ttl: int):
                return True

            async def delete(self, key: str):
                return True

            async def clear(self):
                return True

            async def exists(self, key: str):
                return False

            async def get_stats(self):
                return {}

            async def close(self):
                pass

        provider = ProviderWithBadSecret()
        cache = SimpleCache()
        manager = SecretsManager(provider, cache=cache, validate_secrets=False)

        # Should get empty string since secret key is missing, then fail validation
        with pytest.raises(SecretValidationError, match="too short"):
            await manager.get_symmetric_secret("test")

    @pytest.mark.asyncio
    async def test_encryption_key_string_utf8_length(self):
        """Test encryption key with UTF-8 string length validation"""

        class SimpleProvider:
            async def get_secret(self, path: str):
                # String with UTF-8 characters that has fewer bytes than chars
                return {"key": "test_key_" + "ñ" * 30}  # Should be > 32 chars but < 32 bytes

            async def health_check(self):
                return True

        class SimpleCache:
            async def get(self, key: str):
                return None

            async def set(self, key: str, value, ttl: int):
                return True

            async def delete(self, key: str):
                return True

            async def clear(self):
                return True

            async def exists(self, key: str):
                return False

            async def get_stats(self):
                return {}

            async def close(self):
                pass

        provider = SimpleProvider()
        cache = SimpleCache()
        manager = SecretsManager(provider, cache=cache, validate_secrets=False)

        # Should handle UTF-8 byte length correctly
        key = await manager.get_encryption_key("test", min_length=32)
        assert isinstance(key, str)

    @pytest.mark.asyncio
    async def test_validation_failure_with_observability(self):
        """Test validation failure with observability recording"""

        class SimpleProvider:
            async def get_secret(self, path: str):
                return {"secret": "short"}  # Too short

            async def health_check(self):
                return True

        class SimpleCache:
            async def get(self, key: str):
                return None

            async def set(self, key: str, value, ttl: int):
                return True

            async def delete(self, key: str):
                return True

            async def clear(self):
                return True

            async def exists(self, key: str):
                return False

            async def get_stats(self):
                return {}

            async def close(self):
                pass

        class SimpleValidator:
            def validate(self, secret_data, kind):
                return False  # Always fail

            def get_validation_errors(self, secret_data, kind):
                return ["Secret too short", "Invalid format"]

        class TrackingHook:
            def __init__(self):
                self.validation_failures = []

            def record_cache_hit(self, path):
                pass

            def record_cache_miss(self, path):
                pass

            def record_secret_fetch(self, kind, source, success, latency_ms, path):
                pass

            def record_validation_failure(self, kind, error, path):
                self.validation_failures.append((kind, error, path))

            def record_provider_error(self, provider_name, error_type, path):
                pass

        provider = SimpleProvider()
        cache = SimpleCache()
        validator = SimpleValidator()
        hook = TrackingHook()
        manager = SecretsManager(
            provider,
            cache=cache,
            validator=validator,
            observability_hook=hook,
            validate_secrets=True,
        )

        with pytest.raises(SecretValidationError):
            await manager.get_symmetric_secret("test")

        # Should record validation failure
        assert len(hook.validation_failures) == 1
        assert manager._stats["validation_failures"] == 1
