"""Event bus adapters."""

from .base import AdapterConfig, AdapterMetadata, BaseAdapter
from .memory import MemoryConfig, MemoryEventBus, create_memory_bus

__all__ = [
    "AdapterConfig",
    "AdapterMetadata",
    "BaseAdapter",
    "MemoryConfig",
    "MemoryEventBus",
    "create_memory_bus",
]

# Optional Redis adapter
try:
    from .redis_streams import RedisConfig, RedisEventBus, create_redis_bus  # noqa: F401

    __all__.extend(["RedisConfig", "RedisEventBus", "create_redis_bus"])
except ImportError:
    pass

# Optional Kafka adapter
try:
    from .kafka import KafkaConfig, KafkaEventBus, create_kafka_bus  # noqa: F401

    __all__.extend(["KafkaConfig", "KafkaEventBus", "create_kafka_bus"])
except ImportError:
    pass
