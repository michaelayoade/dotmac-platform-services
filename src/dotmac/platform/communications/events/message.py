"""Core message types and codecs for the event bus."""

import uuid
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Protocol

__all__ = [
    "Event",
    "MessageCodec",
    "EventMetadata",
]


@dataclass(frozen=True)
class EventMetadata:
    """Metadata for event messages."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    content_type: str = "application/json"
    encoding: str = "utf-8"
    producer: Optional[str] = None
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None

    def to_headers(self) -> dict[str, str]:
        """Convert metadata to transport headers."""
        headers = {
            "x-event-id": str(self.id),
            "x-timestamp": self.timestamp.isoformat(),
            "content-type": self.content_type,
            "encoding": self.encoding,
        }

        if self.producer:
            headers["x-producer"] = self.producer
        if self.correlation_id:
            headers["x-correlation-id"] = self.correlation_id
        if self.causation_id:
            headers["x-causation-id"] = self.causation_id

        return headers

    @classmethod
    def from_headers(cls, headers: dict[str, str]) -> "EventMetadata":
        """Create metadata from transport headers."""
        # Normalize header keys to lowercase
        headers_lower = {k.lower(): v for k, v in headers.items()}

        # Parse timestamp
        timestamp_str = headers_lower.get("x-timestamp")
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        else:
            timestamp = datetime.utcnow()

        # Parse UUID
        event_id_str = headers_lower.get("x-event-id")
        if event_id_str:
            event_id = uuid.UUID(event_id_str)
        else:
            event_id = uuid.uuid4()

        return cls(
            id=event_id,
            timestamp=timestamp,
            content_type=headers_lower.get("content-type", "application/json"),
            encoding=headers_lower.get("encoding", "utf-8"),
            producer=headers_lower.get("x-producer"),
            correlation_id=headers_lower.get("x-correlation-id"),
            causation_id=headers_lower.get("x-causation-id"),
        )


@dataclass
class Event:
    """
    Core event message structure.

    An Event represents a message that can be published to and consumed from
    an event bus. It contains both the business payload and transport metadata.
    """

    topic: str
    payload: dict[str, Any]
    key: Optional[str] = None
    headers: Optional[dict[str, str]] = None
    tenant_id: Optional[str] = None
    metadata: Optional[EventMetadata] = None
    event_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize default values after creation."""
        if self.headers is None:
            self.headers = {}

        if self.metadata is None:
            self.metadata = EventMetadata()

        # Add tenant_id to headers if provided
        if self.tenant_id:
            self.headers["x-tenant-id"] = self.tenant_id

    @property
    def id(self) -> uuid.UUID:
        """Event unique identifier."""
        return self.metadata.id if self.metadata else uuid.uuid4()

    @property
    def timestamp(self) -> datetime:
        """Event timestamp."""
        return self.metadata.timestamp if self.metadata else datetime.utcnow()

    def with_headers(self, **headers: str) -> "Event":
        """Create a copy of the event with additional headers."""
        new_headers = (self.headers or {}).copy()
        new_headers.update(headers)

        return Event(
            topic=self.topic,
            payload=self.payload,
            key=self.key,
            headers=new_headers,
            tenant_id=self.tenant_id,
            metadata=self.metadata,
        )

    def with_metadata(self, **metadata_kwargs: Any) -> "Event":
        """Create a copy of the event with updated metadata."""
        if self.metadata:
            # Create new metadata with updated fields
            current_metadata = self.metadata
            metadata_dict = {
                "id": current_metadata.id,
                "timestamp": current_metadata.timestamp,
                "content_type": current_metadata.content_type,
                "encoding": current_metadata.encoding,
                "producer": current_metadata.producer,
                "correlation_id": current_metadata.correlation_id,
                "causation_id": current_metadata.causation_id,
            }
            metadata_dict.update(metadata_kwargs)
            new_metadata = EventMetadata(**metadata_dict)
        else:
            new_metadata = EventMetadata(**metadata_kwargs)

        return Event(
            topic=self.topic,
            payload=self.payload,
            key=self.key,
            headers=self.headers,
            tenant_id=self.tenant_id,
            metadata=new_metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize event to dictionary for transport."""
        result = {
            "topic": self.topic,
            "payload": self.payload,
        }

        if self.key is not None:
            result["key"] = self.key

        if self.headers:
            result["headers"] = self.headers

        if self.tenant_id:
            result["tenant_id"] = self.tenant_id

        if self.metadata:
            result["metadata"] = {
                "id": str(self.metadata.id),
                "timestamp": self.metadata.timestamp.isoformat(),
                "content_type": self.metadata.content_type,
                "encoding": self.metadata.encoding,
            }

            if self.metadata.producer:
                result["metadata"]["producer"] = self.metadata.producer
            if self.metadata.correlation_id:
                result["metadata"]["correlation_id"] = self.metadata.correlation_id
            if self.metadata.causation_id:
                result["metadata"]["causation_id"] = self.metadata.causation_id

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        """Deserialize event from dictionary."""
        metadata = None
        if "metadata" in data:
            meta_data = data["metadata"]
            metadata = EventMetadata(
                id=uuid.UUID(meta_data["id"]),
                timestamp=datetime.fromisoformat(meta_data["timestamp"].replace("Z", "+00:00")),
                content_type=meta_data.get("content_type", "application/json"),
                encoding=meta_data.get("encoding", "utf-8"),
                producer=meta_data.get("producer"),
                correlation_id=meta_data.get("correlation_id"),
                causation_id=meta_data.get("causation_id"),
            )

        return cls(
            topic=data["topic"],
            payload=data["payload"],
            key=data.get("key"),
            headers=data.get("headers"),
            tenant_id=data.get("tenant_id"),
            metadata=metadata,
        )


class MessageCodec(Protocol):
    """Protocol for encoding and decoding event messages."""

    @abstractmethod
    def encode(self, event: Event | dict[str, Any]) -> bytes:
        """Encode an event or dictionary to bytes for transport."""
        ...

    @abstractmethod
    def decode(self, data: bytes) -> Event | dict[str, Any]:
        """Decode bytes to an event or dictionary."""
        ...

    @property
    @abstractmethod
    def content_type(self) -> str:
        """Content type identifier for this codec."""
        ...
