"""
EventStore async class: append, load_stream, load_all, stream_version,
archive_stream, get_stream_metadata. Optimistic concurrency via expected_version.
Outbox writes in same transaction.
"""
from __future__ import annotations

from typing import AsyncIterator
from src.models.events import BaseEvent, StoredEvent, StreamMetadata


class EventStore:
    """Async event store backed by PostgreSQL."""

    async def append(
        self,
        stream_id: str,
        events: list[BaseEvent],
        expected_version: int,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> int:
        """
        Atomically appends events to stream_id.
        Raises OptimisticConcurrencyError if stream version != expected_version.
        Writes to outbox in same transaction.
        Returns new stream version.
        """
        raise NotImplementedError

    async def load_stream(
        self,
        stream_id: str,
        from_position: int = 0,
        to_position: int | None = None,
    ) -> list[StoredEvent]:
        """Load events in stream order, upcasted."""
        raise NotImplementedError

    async def load_all(
        self,
        from_global_position: int = 0,
        event_types: list[str] | None = None,
        batch_size: int = 500,
    ) -> AsyncIterator[StoredEvent]:
        """Async generator for efficient replay."""
        raise NotImplementedError

    async def stream_version(self, stream_id: str) -> int:
        raise NotImplementedError

    async def archive_stream(self, stream_id: str) -> None:
        raise NotImplementedError

    async def get_stream_metadata(self, stream_id: str) -> StreamMetadata | None:
        raise NotImplementedError
