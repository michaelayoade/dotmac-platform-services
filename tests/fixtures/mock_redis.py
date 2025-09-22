"""
Mock Redis Fixtures for Testing
Provides Redis client mocks and cache-related test utilities.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union
from unittest.mock import AsyncMock, Mock

import pytest


class MockRedis:
    """
    Mock Redis client with common operations.
    Implements both sync and async interfaces.
    """

    def __init__(self, **kwargs):
        self.data: Dict[str, Any] = {}
        self.expiry: Dict[str, datetime] = {}
        self.connected = True
        self.pipeline_mode = False
        self.pipeline_commands: List[tuple] = []
        self.pubsub_channels: Dict[str, List[Any]] = {}
        self.lists: Dict[str, List[str]] = {}
        self.sets: Dict[str, Set[str]] = {}
        self.hashes: Dict[str, Dict[str, str]] = {}
        self.streams: Dict[str, List[Dict]] = {}
        self.call_history: List[Dict[str, Any]] = []

    async def get(self, key: str) -> Optional[bytes]:
        """Get value by key."""
        self.call_history.append({"method": "get", "args": {"key": key}})
        self._check_expiry(key)
        value = self.data.get(key)
        if value is not None and not isinstance(value, bytes):
            return str(value).encode()
        return value

    async def set(
        self,
        key: str,
        value: Union[str, bytes, int],
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """Set key-value with optional expiry."""
        self.call_history.append({
            "method": "set",
            "args": {"key": key, "value": value, "ex": ex, "px": px, "nx": nx, "xx": xx}
        })

        if nx and key in self.data:
            return False
        if xx and key not in self.data:
            return False

        if isinstance(value, (str, int)):
            value = str(value).encode()

        self.data[key] = value

        if ex:
            self.expiry[key] = datetime.now() + timedelta(seconds=ex)
        elif px:
            self.expiry[key] = datetime.now() + timedelta(milliseconds=px)

        return True

    async def delete(self, *keys: str) -> int:
        """Delete keys."""
        self.call_history.append({"method": "delete", "args": {"keys": keys}})
        deleted = 0
        for key in keys:
            if key in self.data:
                del self.data[key]
                deleted += 1
            if key in self.expiry:
                del self.expiry[key]
        return deleted

    async def exists(self, *keys: str) -> int:
        """Check if keys exist."""
        self.call_history.append({"method": "exists", "args": {"keys": keys}})
        count = 0
        for key in keys:
            self._check_expiry(key)
            if key in self.data:
                count += 1
        return count

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiry for a key."""
        self.call_history.append({"method": "expire", "args": {"key": key, "seconds": seconds}})
        if key in self.data:
            self.expiry[key] = datetime.now() + timedelta(seconds=seconds)
            return True
        return False

    async def ttl(self, key: str) -> int:
        """Get time to live for a key."""
        self.call_history.append({"method": "ttl", "args": {"key": key}})
        if key not in self.data:
            return -2
        if key not in self.expiry:
            return -1
        remaining = (self.expiry[key] - datetime.now()).total_seconds()
        if remaining <= 0:
            self._check_expiry(key)
            return -2
        return int(remaining)

    async def incr(self, key: str) -> int:
        """Increment integer value."""
        self.call_history.append({"method": "incr", "args": {"key": key}})
        self._check_expiry(key)
        current = int(self.data.get(key, 0))
        current += 1
        self.data[key] = str(current).encode()
        return current

    async def decr(self, key: str) -> int:
        """Decrement integer value."""
        self.call_history.append({"method": "decr", "args": {"key": key}})
        self._check_expiry(key)
        current = int(self.data.get(key, 0))
        current -= 1
        self.data[key] = str(current).encode()
        return current

    async def hget(self, name: str, key: str) -> Optional[bytes]:
        """Get hash field value."""
        self.call_history.append({"method": "hget", "args": {"name": name, "key": key}})
        hash_data = self.hashes.get(name, {})
        value = hash_data.get(key)
        return value.encode() if value else None

    async def hset(self, name: str, key: str, value: str) -> int:
        """Set hash field value."""
        self.call_history.append({"method": "hset", "args": {"name": name, "key": key, "value": value}})
        if name not in self.hashes:
            self.hashes[name] = {}
        is_new = key not in self.hashes[name]
        self.hashes[name][key] = str(value)
        return 1 if is_new else 0

    async def hgetall(self, name: str) -> Dict[bytes, bytes]:
        """Get all hash fields and values."""
        self.call_history.append({"method": "hgetall", "args": {"name": name}})
        hash_data = self.hashes.get(name, {})
        return {k.encode(): v.encode() for k, v in hash_data.items()}

    async def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields."""
        self.call_history.append({"method": "hdel", "args": {"name": name, "keys": keys}})
        if name not in self.hashes:
            return 0
        deleted = 0
        for key in keys:
            if key in self.hashes[name]:
                del self.hashes[name][key]
                deleted += 1
        return deleted

    async def sadd(self, key: str, *values: str) -> int:
        """Add members to set."""
        self.call_history.append({"method": "sadd", "args": {"key": key, "values": values}})
        if key not in self.sets:
            self.sets[key] = set()
        added = 0
        for value in values:
            if value not in self.sets[key]:
                self.sets[key].add(value)
                added += 1
        return added

    async def smembers(self, key: str) -> Set[bytes]:
        """Get all set members."""
        self.call_history.append({"method": "smembers", "args": {"key": key}})
        members = self.sets.get(key, set())
        return {m.encode() for m in members}

    async def srem(self, key: str, *values: str) -> int:
        """Remove members from set."""
        self.call_history.append({"method": "srem", "args": {"key": key, "values": values}})
        if key not in self.sets:
            return 0
        removed = 0
        for value in values:
            if value in self.sets[key]:
                self.sets[key].remove(value)
                removed += 1
        return removed

    async def lpush(self, key: str, *values: str) -> int:
        """Push values to list head."""
        self.call_history.append({"method": "lpush", "args": {"key": key, "values": values}})
        if key not in self.lists:
            self.lists[key] = []
        for value in reversed(values):
            self.lists[key].insert(0, value)
        return len(self.lists[key])

    async def rpush(self, key: str, *values: str) -> int:
        """Push values to list tail."""
        self.call_history.append({"method": "rpush", "args": {"key": key, "values": values}})
        if key not in self.lists:
            self.lists[key] = []
        self.lists[key].extend(values)
        return len(self.lists[key])

    async def lpop(self, key: str) -> Optional[bytes]:
        """Pop from list head."""
        self.call_history.append({"method": "lpop", "args": {"key": key}})
        if key in self.lists and self.lists[key]:
            return self.lists[key].pop(0).encode()
        return None

    async def lrange(self, key: str, start: int, stop: int) -> List[bytes]:
        """Get list range."""
        self.call_history.append({"method": "lrange", "args": {"key": key, "start": start, "stop": stop}})
        list_data = self.lists.get(key, [])
        if stop == -1:
            stop = len(list_data)
        else:
            stop += 1
        return [v.encode() for v in list_data[start:stop]]

    async def flushdb(self) -> bool:
        """Clear all data."""
        self.call_history.append({"method": "flushdb", "args": {}})
        self.data.clear()
        self.expiry.clear()
        self.hashes.clear()
        self.sets.clear()
        self.lists.clear()
        self.streams.clear()
        return True

    async def ping(self) -> bool:
        """Check connection."""
        self.call_history.append({"method": "ping", "args": {}})
        return self.connected

    async def keys(self, pattern: str = "*") -> List[bytes]:
        """Get keys matching pattern."""
        self.call_history.append({"method": "keys", "args": {"pattern": pattern}})
        import fnmatch
        all_keys = set(self.data.keys()) | set(self.hashes.keys()) | set(self.sets.keys()) | set(self.lists.keys())

        if pattern == "*":
            return [k.encode() for k in all_keys]

        matching = [k for k in all_keys if fnmatch.fnmatch(k, pattern)]
        return [k.encode() for k in matching]

    async def publish(self, channel: str, message: Any) -> int:
        """Publish message to a channel."""
        self.call_history.append({"method": "publish", "args": {"channel": channel, "message": message}})
        encoded = message if isinstance(message, str) else json.dumps(message)
        self.pubsub_channels.setdefault(channel, []).append(encoded)
        return len(self.pubsub_channels[channel])

    async def subscribe(self, *channels: str) -> None:
        """Subscribe to channels."""
        self.call_history.append({"method": "subscribe", "args": {"channels": channels}})
        for channel in channels:
            self.pubsub_channels.setdefault(channel, [])

    async def unsubscribe(self, *channels: str) -> None:
        """Unsubscribe from channels."""
        self.call_history.append({"method": "unsubscribe", "args": {"channels": channels}})
        for channel in channels:
            self.pubsub_channels.pop(channel, None)

    def pipeline(self):
        """Create pipeline for batch operations."""
        return MockRedisPipeline(self)

    async def close(self):
        """Close connection."""
        self.connected = False

    def _check_expiry(self, key: str):
        """Check and remove expired keys."""
        if key in self.expiry:
            if datetime.now() >= self.expiry[key]:
                if key in self.data:
                    del self.data[key]
                del self.expiry[key]

    async def setex(self, key: str, seconds: int, value: Union[str, bytes]) -> bool:
        """Set with expiry in seconds."""
        return await self.set(key, value, ex=seconds)

    async def mget(self, *keys: str) -> List[Optional[bytes]]:
        """Get multiple keys."""
        self.call_history.append({"method": "mget", "args": {"keys": keys}})
        results = []
        for key in keys:
            value = await self.get(key)
            results.append(value)
        return results

    async def mset(self, mapping: Dict[str, Union[str, bytes]]) -> bool:
        """Set multiple keys."""
        self.call_history.append({"method": "mset", "args": {"mapping": mapping}})
        for key, value in mapping.items():
            await self.set(key, value)
        return True


class MockRedisPipeline:
    """Mock Redis pipeline for batch operations."""

    def __init__(self, redis: MockRedis):
        self.redis = redis
        self.commands: List[tuple] = []

    def set(self, key: str, value: Union[str, bytes], ex: Optional[int] = None):
        self.commands.append(("set", key, value, ex))
        return self

    def get(self, key: str):
        self.commands.append(("get", key))
        return self

    def delete(self, *keys: str):
        self.commands.append(("delete", *keys))
        return self

    def incr(self, key: str):
        self.commands.append(("incr", key))
        return self

    async def execute(self) -> List[Any]:
        """Execute all pipeline commands."""
        results = []
        for command in self.commands:
            cmd_name = command[0]
            cmd_args = command[1:]

            if cmd_name == "set":
                if len(cmd_args) >= 3 and cmd_args[2] is not None:
                    result = await self.redis.set(cmd_args[0], cmd_args[1], ex=cmd_args[2])
                else:
                    result = await self.redis.set(cmd_args[0], cmd_args[1])
                results.append(result)
            elif cmd_name == "get":
                result = await self.redis.get(cmd_args[0])
                results.append(result)
            elif cmd_name == "delete":
                result = await self.redis.delete(*cmd_args)
                results.append(result)
            elif cmd_name == "incr":
                result = await self.redis.incr(cmd_args[0])
                results.append(result)

        self.commands.clear()
        return results


class MockRedisLock:
    """Mock Redis distributed lock."""

    def __init__(self, redis: MockRedis, key: str, timeout: int = 10):
        self.redis = redis
        self.key = f"lock:{key}"
        self.timeout = timeout
        self.acquired = False

    async def __aenter__(self):
        """Acquire lock."""
        self.acquired = await self.redis.set(self.key, "1", nx=True, ex=self.timeout)
        if not self.acquired:
            raise Exception(f"Could not acquire lock for {self.key}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release lock."""
        if self.acquired:
            await self.redis.delete(self.key)
            self.acquired = False


class MockRedisPubSub:
    """Mock Redis pub/sub functionality."""

    def __init__(self, redis: MockRedis):
        self.redis = redis
        self.subscriptions: Set[str] = set()
        self.messages: List[Dict] = []

    async def subscribe(self, *channels: str):
        """Subscribe to channels."""
        self.subscriptions.update(channels)
        for channel in channels:
            if channel not in self.redis.pubsub_channels:
                self.redis.pubsub_channels[channel] = []

    async def unsubscribe(self, *channels: str):
        """Unsubscribe from channels."""
        for channel in channels:
            self.subscriptions.discard(channel)

    async def publish(self, channel: str, message: str) -> int:
        """Publish message to channel."""
        if channel in self.redis.pubsub_channels:
            self.redis.pubsub_channels[channel].append(message)
            return len(self.redis.pubsub_channels[channel])
        return 0

    async def get_message(self, timeout: Optional[float] = None) -> Optional[Dict]:
        """Get next message from subscribed channels."""
        if self.messages:
            return self.messages.pop(0)

        for channel in self.subscriptions:
            if channel in self.redis.pubsub_channels and self.redis.pubsub_channels[channel]:
                message = self.redis.pubsub_channels[channel].pop(0)
                return {
                    "type": "message",
                    "channel": channel,
                    "data": message
                }
        return None


@pytest.fixture
def mock_redis():
    """Fixture providing a mock Redis client."""
    redis = MockRedis()

    async def _wrap(name: str, *args, **kwargs):
        return await getattr(MockRedis, name)(redis, *args, **kwargs)

    redis.get = AsyncMock(side_effect=lambda key: _wrap("get", key))
    redis.set = AsyncMock(side_effect=lambda key, value, **kwargs: _wrap("set", key, value, **kwargs))
    redis.delete = AsyncMock(side_effect=lambda *keys: _wrap("delete", *keys))
    redis.publish = AsyncMock(side_effect=lambda channel, message: _wrap("publish", channel, message))
    redis.subscribe = AsyncMock(side_effect=lambda *channels: _wrap("subscribe", *channels))
    redis.unsubscribe = AsyncMock(side_effect=lambda *channels: _wrap("unsubscribe", *channels))
    redis.ping = AsyncMock(side_effect=lambda: _wrap("ping"))

    return redis


@pytest.fixture
def mock_redis_with_data(mock_redis):
    """Fixture providing a mock Redis client with test data."""
    # Add some test data
    mock_redis.data = {
        "test:key1": b"value1",
        "test:key2": b"value2",
        "counter": b"10",
    }
    mock_redis.hashes = {
        "test:hash": {
            "field1": "value1",
            "field2": "value2",
        }
    }
    mock_redis.sets = {
        "test:set": {"member1", "member2", "member3"}
    }
    mock_redis.lists = {
        "test:list": ["item1", "item2", "item3"]
    }
    return mock_redis


@pytest.fixture
def mock_redis_pipeline(mock_redis):
    """Fixture providing a mock Redis pipeline."""
    return MockRedisPipeline(mock_redis)


@pytest.fixture
def mock_redis_lock(mock_redis):
    """Fixture providing a mock Redis lock."""
    return MockRedisLock(mock_redis, "test-resource")
