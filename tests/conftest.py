"""Pytest fixtures for integration tests."""
from __future__ import annotations

import os

import pytest

from src.event_store import EventStore


@pytest.fixture
def db_url() -> str:
    return os.environ.get("DATABASE_URL", "")


@pytest.fixture
async def store(db_url: str) -> EventStore:
    if not db_url:
        pytest.skip("DATABASE_URL is not set; skipping DB integration tests.")
    event_store = EventStore(db_url)
    await event_store.connect()
    try:
        schema_path = os.path.join(os.path.dirname(__file__), "..", "src", "schema.sql")
        with open(schema_path, encoding="utf-8") as f:
            schema_sql = f.read()
        pool = await event_store._pool_or_raise()
        async with pool.acquire() as conn:
            await conn.execute(schema_sql)
            # Reset both write-side and read-side state for deterministic tests.
            await conn.execute(
                """
                TRUNCATE TABLE
                    outbox,
                    events,
                    event_streams,
                    projection_checkpoints,
                    projection_application_summary,
                    projection_agent_performance,
                    projection_compliance_audit
                RESTART IDENTITY CASCADE
                """
            )
        yield event_store
    finally:
        await event_store.close()
