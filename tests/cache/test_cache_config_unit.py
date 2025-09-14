import pytest

from dotmac.platform.cache.config import CacheConfig


@pytest.mark.unit
def test_redis_connection_url_builder_defaults_and_ssl_auth():
    # Default without explicit URL
    cfg = CacheConfig()
    url = cfg.redis_connection_url
    assert url == "redis://localhost:6379/0"

    # With SSL and password
    cfg2 = CacheConfig(redis_ssl=True, redis_password="s3cr3t", redis_host="example.com", redis_port=6380, redis_db=2)
    assert cfg2.redis_connection_url == "rediss://:s3cr3t@example.com:6380/2"

    # With explicit URL override
    cfg3 = CacheConfig(redis_url="redis://my:6379/5")
    assert cfg3.redis_connection_url == "redis://my:6379/5"

