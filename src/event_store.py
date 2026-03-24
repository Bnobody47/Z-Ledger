"""Async PostgreSQL event store with optimistic concurrency."""
from __future__ import annotations

import json
from typing import Any, AsyncIterator

import asyncpg

from src.models.events import (
    BaseEvent,
    OptimisticConcurrencyError,
    StoredEvent,
    StreamMetadata,
)
from src.upcasting.registry import UpcasterRegistry
from src.upcasting.upcasters import registry as default_upcaster_registry


def _row_to_stored_event(row: asyncpg.Record) -> dict:
    """Convert DB row to dict suitable for StoredEvent; parse JSONB if returned as str."""
    d = dict(row)
    if isinstance(d.get("payload"), str):
        d["payload"] = json.loads(d["payload"])
    if isinstance(d.get("metadata"), str):
        d["metadata"] = json.loads(d["metadata"])
    return d


def _infer_aggregate_type(stream_id: str) -> str:
    if stream_id.startswith("loan-"):
        return "LoanApplication"
    if stream_id.startswith("agent-"):
        return "AgentSession"
    if stream_id.startswith("compliance-"):
        return "ComplianceRecord"
    if stream_id.startswith("audit-"):
        return "AuditLedger"
    return "Unknown"


class EventStore:
    def __init__(self, database_url: str, upcaster_registry: UpcasterRegistry | None = None):
        self._database_url = database_url
        self._pool: asyncpg.Pool | None = None
        self._upcaster_registry = upcaster_registry or default_upcaster_registry

    async def connect(self) -> None:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(dsn=self._database_url, min_size=1, max_size=10)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def _pool_or_raise(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("EventStore is not connected. Call connect() first.")
        return self._pool

    async def append(
        self,
        stream_id: str,
        events: list[BaseEvent],
        expected_version: int,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> int:
        if not events:
            return await self.stream_version(stream_id)

        pool = await self._pool_or_raise()
        async with pool.acquire() as conn:
            async with conn.transaction():
                stream_row = await conn.fetchrow(
                    "SELECT stream_id, current_version FROM event_streams WHERE stream_id = $1 FOR UPDATE",
                    stream_id,
                )
                if stream_row is None:
                    if expected_version != -1:
                        raise OptimisticConcurrencyError(
                            "Expected existing stream but stream does not exist",
                            stream_id,
                            expected_version,
                            0,
                        )
                    await conn.execute(
                        """
                        INSERT INTO event_streams (stream_id, aggregate_type, current_version, metadata)
                        VALUES ($1, $2, 0, '{}'::jsonb)
                        """,
                        stream_id,
                        _infer_aggregate_type(stream_id),
                    )
                    current_version = 0
                else:
                    current_version = int(stream_row["current_version"])
                    if current_version != expected_version:
                        raise OptimisticConcurrencyError(
                            "Stream version mismatch during append",
                            stream_id,
                            expected_version,
                            current_version,
                        )

                metadata = {"correlation_id": correlation_id, "causation_id": causation_id}
                new_version = current_version
                for event in events:
                    new_version += 1
                    row = await conn.fetchrow(
                        """
                        INSERT INTO events (
                            stream_id, stream_position, event_type, event_version, payload, metadata
                        ) VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb)
                        RETURNING event_id
                        """,
                        stream_id,
                        new_version,
                        event.event_type,
                        event.event_version,
                        json.dumps(event.payload()),
                        json.dumps(metadata),
                    )
                    await conn.execute(
                        """
                        INSERT INTO outbox (event_id, destination, payload)
                        VALUES ($1, $2, $3::jsonb)
                        """,
                        row["event_id"],
                        "internal:projection-daemon",
                        json.dumps(
                            {
                                "stream_id": stream_id,
                                "event_type": event.event_type,
                                "stream_position": new_version,
                            }
                        ),
                    )

                await conn.execute(
                    "UPDATE event_streams SET current_version = $2 WHERE stream_id = $1",
                    stream_id,
                    new_version,
                )
                return new_version

    async def load_stream(
        self,
        stream_id: str,
        from_position: int = 0,
        to_position: int | None = None,
    ) -> list[StoredEvent]:
        pool = await self._pool_or_raise()
        async with pool.acquire() as conn:
            if to_position is None:
                rows = await conn.fetch(
                    """
                    SELECT event_id, stream_id, stream_position, global_position, event_type, event_version,
                           payload, metadata, recorded_at
                    FROM events
                    WHERE stream_id = $1 AND stream_position > $2
                    ORDER BY stream_position ASC
                    """,
                    stream_id,
                    from_position,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT event_id, stream_id, stream_position, global_position, event_type, event_version,
                           payload, metadata, recorded_at
                    FROM events
                    WHERE stream_id = $1 AND stream_position > $2 AND stream_position <= $3
                    ORDER BY stream_position ASC
                    """,
                    stream_id,
                    from_position,
                    to_position,
                )
        out: list[StoredEvent] = []
        for row in rows:
            event = StoredEvent(**_row_to_stored_event(row))
            out.append(self._upcaster_registry.upcast(event))
        return out

    async def load_all(
        self,
        from_global_position: int = 0,
        event_types: list[str] | None = None,
        batch_size: int = 500,
    ) -> AsyncIterator[StoredEvent]:
        pool = await self._pool_or_raise()
        position = from_global_position
        while True:
            async with pool.acquire() as conn:
                if event_types:
                    rows = await conn.fetch(
                        """
                        SELECT event_id, stream_id, stream_position, global_position, event_type, event_version,
                               payload, metadata, recorded_at
                        FROM events
                        WHERE global_position > $1 AND event_type = ANY($2::text[])
                        ORDER BY global_position ASC
                        LIMIT $3
                        """,
                        position,
                        event_types,
                        batch_size,
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT event_id, stream_id, stream_position, global_position, event_type, event_version,
                               payload, metadata, recorded_at
                        FROM events
                        WHERE global_position > $1
                        ORDER BY global_position ASC
                        LIMIT $2
                        """,
                        position,
                        batch_size,
                    )
            if not rows:
                break
            for row in rows:
                event = StoredEvent(**_row_to_stored_event(row))
                event = self._upcaster_registry.upcast(event)
                position = event.global_position
                yield event

    async def stream_version(self, stream_id: str) -> int:
        pool = await self._pool_or_raise()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT current_version FROM event_streams WHERE stream_id = $1",
                stream_id,
            )
        return 0 if row is None else int(row["current_version"])

    async def stream_exists(self, stream_id: str) -> bool:
        pool = await self._pool_or_raise()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM event_streams WHERE stream_id = $1",
                stream_id,
            )
        return row is not None

    async def archive_stream(self, stream_id: str) -> None:
        pool = await self._pool_or_raise()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE event_streams SET archived_at = NOW() WHERE stream_id = $1",
                stream_id,
            )

    async def get_stream_metadata(self, stream_id: str) -> StreamMetadata | None:
        pool = await self._pool_or_raise()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT stream_id, aggregate_type, current_version, created_at, archived_at, metadata
                FROM event_streams
                WHERE stream_id = $1
                """,
                stream_id,
            )
        if row is None:
            return None
        return StreamMetadata(**dict(row))

    async def execute(self, query: str, *args: Any) -> str:
        pool = await self._pool_or_raise()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        pool = await self._pool_or_raise()
        async with pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> asyncpg.Record | None:
        pool = await self._pool_or_raise()
        async with pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
