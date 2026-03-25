"""
ProjectionDaemon: fault-tolerant batch processing, per-projection checkpoints,
configurable retry, get_lag() per projection.
"""
from __future__ import annotations

import asyncio
import json

from src.event_store import EventStore


class Projection:
    """Base for projections. Subclasses implement handle(event)."""

    name: str

    async def handle(self, event, store: EventStore) -> None:
        raise NotImplementedError


class ProjectionDaemon:
    def __init__(self, store: EventStore, projections: list[Projection], max_retries: int = 3):
        self._store = store
        self._projections = {p.name: p for p in projections}
        self._running = False
        self._max_retries = max_retries
        self._lags: dict[str, float] = {p.name: 0.0 for p in projections}

    async def run_forever(self, poll_interval_ms: int = 100) -> None:
        self._running = True
        while self._running:
            await self._process_batch()
            await asyncio.sleep(poll_interval_ms / 1000)

    def stop(self) -> None:
        self._running = False

    async def _process_batch(self) -> None:
        for projection_name, projection in self._projections.items():
            checkpoint = await self._store.fetchrow(
                "SELECT last_position FROM projection_checkpoints WHERE projection_name = $1",
                projection_name,
            )
            last_position = int(checkpoint["last_position"]) if checkpoint else 0
            rows = await self._store.fetch(
                """
                SELECT event_id, stream_id, stream_position, global_position, event_type, event_version,
                       payload, metadata, recorded_at
                FROM events
                WHERE global_position > $1
                ORDER BY global_position ASC
                LIMIT 500
                """,
                last_position,
            )
            if not rows:
                latest = await self._store.fetchrow("SELECT COALESCE(MAX(global_position), 0) AS max_pos FROM events")
                self._lags[projection_name] = float(int(latest["max_pos"]) - last_position)
                continue

            for row in rows:
                from src.models.events import StoredEvent

                d = dict(row)
                # asyncpg returns JSONB columns as strings unless type codecs are registered.
                # Convert back to dicts so Pydantic can validate.
                if isinstance(d.get("payload"), str):
                    d["payload"] = json.loads(d["payload"])
                if isinstance(d.get("metadata"), str):
                    d["metadata"] = json.loads(d["metadata"])

                event = StoredEvent(**d)
                attempts = 0
                while True:
                    try:
                        await projection.handle(event, self._store)
                        await self._store.execute(
                            """
                            INSERT INTO projection_checkpoints (projection_name, last_position, updated_at)
                            VALUES ($1, $2, NOW())
                            ON CONFLICT (projection_name)
                            DO UPDATE SET last_position = EXCLUDED.last_position, updated_at = NOW()
                            """,
                            projection_name,
                            event.global_position,
                        )
                        last_position = event.global_position
                        break
                    except Exception:
                        attempts += 1
                        if attempts > self._max_retries:
                            # Skip poison event after retry budget, keep daemon alive.
                            await self._store.execute(
                                """
                                INSERT INTO projection_checkpoints (projection_name, last_position, updated_at)
                                VALUES ($1, $2, NOW())
                                ON CONFLICT (projection_name)
                                DO UPDATE SET last_position = EXCLUDED.last_position, updated_at = NOW()
                                """,
                                projection_name,
                                event.global_position,
                            )
                            last_position = event.global_position
                            break

            latest = await self._store.fetchrow("SELECT COALESCE(MAX(global_position), 0) AS max_pos FROM events")
            self._lags[projection_name] = float(int(latest["max_pos"]) - last_position)

    def get_lag(self, projection_name: str) -> float:
        """Lag in milliseconds."""
        return self._lags.get(projection_name, 0.0)
