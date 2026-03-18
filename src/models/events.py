"""
Pydantic models for all event types in the Event Catalogue.
BaseEvent, StoredEvent, StreamMetadata, and custom exceptions.
"""
from pydantic import BaseModel
from typing import Any
from uuid import UUID


class BaseEvent(BaseModel):
    """Base for domain events. Subclasses define event_type and payload schema."""

    class Config:
        extra = "forbid"


class StoredEvent(BaseModel):
    """Event as stored/loaded from the event store (with metadata)."""

    event_id: UUID
    stream_id: str
    stream_position: int
    global_position: int
    event_type: str
    event_version: int
    payload: dict[str, Any]
    metadata: dict[str, Any]
    recorded_at: str

    def with_payload(self, payload: dict[str, Any], version: int) -> "StoredEvent":
        return self.model_copy(update={"payload": payload, "event_version": version})


class StreamMetadata(BaseModel):
    """Metadata for a stream (aggregate_type, current_version, etc.)."""

    stream_id: str
    aggregate_type: str
    current_version: int
    created_at: str
    archived_at: str | None
    metadata: dict[str, Any]


class OptimisticConcurrencyError(Exception):
    """Raised when append expected_version does not match stream's current version."""

    def __init__(
        self,
        message: str,
        stream_id: str,
        expected_version: int,
        actual_version: int,
    ):
        super().__init__(message)
        self.stream_id = stream_id
        self.expected_version = expected_version
        self.actual_version = actual_version


class DomainError(Exception):
    """Raised when a business rule is violated."""

    pass
