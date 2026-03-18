"""
ProjectionDaemon: fault-tolerant batch processing, per-projection checkpoints,
configurable retry, get_lag() per projection.
"""
import asyncio
from src.event_store import EventStore


class Projection:
    """Base for projections. Subclasses implement handle(event)."""

    name: str

    async def handle(self, event) -> None:
        raise NotImplementedError


class ProjectionDaemon:
    def __init__(self, store: EventStore, projections: list[Projection]):
        self._store = store
        self._projections = {p.name: p for p in projections}
        self._running = False

    async def run_forever(self, poll_interval_ms: int = 100) -> None:
        self._running = True
        while self._running:
            await self._process_batch()
            await asyncio.sleep(poll_interval_ms / 1000)

    async def _process_batch(self) -> None:
        raise NotImplementedError

    def get_lag(self, projection_name: str) -> float:
        """Lag in milliseconds."""
        raise NotImplementedError
