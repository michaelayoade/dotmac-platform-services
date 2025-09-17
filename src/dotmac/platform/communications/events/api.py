"""Internal API re-exports for dotmac.events package."""

from .adapters import (
    AdapterConfig,
    AdapterMetadata,
    BaseAdapter,
    MemoryConfig,
    MemoryEventBus,
    create_memory_bus,
)
from .bus import (
    ConsumeError,
    EventBus,
    EventBusError,
    EventHandler,
    NotSupportedError,
    PublishError,
    TimeoutError,
)

# Codecs
from .codecs import JsonCodec

# Consumer and retry logic
from .consumer import (
    BackoffPolicy,
    ConsumerOptions,
    RetryPolicy,
    create_exponential_retry_options,
    create_retry_wrapper,
    create_simple_retry_options,
    run_consumer,
)

# Dead Letter Queue
from .dlq import (
    DLQ,
    DLQConsumer,
    DLQEntry,
    DLQError,
    DLQHandler,
    SimpleDLQ,
    alert_on_dlq_entry,
    create_dlq_consumer,
    create_reprocess_after_delay_filter,
    log_dlq_entry,
)
from .message import Event, EventMetadata, MessageCodec

# Observability
from .observability import (
    ObservabilityHooks,
    ObservabilityMetrics,
    create_default_hooks,
    create_dotmac_observability_hooks,
    no_op_hooks,
)

# Optional Redis adapter
try:
    from .adapters import RedisConfig, RedisEventBus, create_redis_bus  # noqa: F401

    _redis_available = True
    __redis_exports = ["RedisConfig", "RedisEventBus", "create_redis_bus"]
except ImportError:
    _redis_available = False
    __redis_exports = []

# Optional Kafka adapter
try:
    from .adapters import KafkaConfig, KafkaEventBus, create_kafka_bus  # noqa: F401

    _kafka_available = True
    __kafka_exports = ["KafkaConfig", "KafkaEventBus", "create_kafka_bus"]
except ImportError:
    _kafka_available = False
    __kafka_exports = []

__all__ = (
    [
        # Core
        "Event",
        "EventMetadata",
        "MessageCodec",
        "EventBus",
        "EventHandler",
        "EventBusError",
        "PublishError",
        "ConsumeError",
        "TimeoutError",
        "NotSupportedError",
        # Codecs
        "JsonCodec",
        # Adapters
        "AdapterConfig",
        "AdapterMetadata",
        "BaseAdapter",
        "MemoryConfig",
        "MemoryEventBus",
        "create_memory_bus",
        # Consumer
        "ConsumerOptions",
        "BackoffPolicy",
        "RetryPolicy",
        "run_consumer",
        "create_retry_wrapper",
        "create_simple_retry_options",
        "create_exponential_retry_options",
        # DLQ
        "DLQ",
        "SimpleDLQ",
        "DLQEntry",
        "DLQError",
        "DLQHandler",
        "DLQConsumer",
        "create_dlq_consumer",
        "log_dlq_entry",
        "alert_on_dlq_entry",
        "create_reprocess_after_delay_filter",
        # Observability
        "ObservabilityHooks",
        "ObservabilityMetrics",
        "create_default_hooks",
        "create_dotmac_observability_hooks",
        "no_op_hooks",
    ]
    + __redis_exports
    + __kafka_exports
)
