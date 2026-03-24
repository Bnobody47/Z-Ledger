"""Adapted EventStore tests based on apex_ledger_starter coverage."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Literal

import pytest

from src.models.events import BaseEvent, OptimisticConcurrencyError


class SampleEvent(BaseEvent):
    event_type: Literal["TestEvent"] = "TestEvent"
    seq: int


def _event(seq: int) -> SampleEvent:
    return SampleEvent(seq=seq)


@pytest.mark.asyncio
async def test_append_new_stream(store):
    stream_id = "test-new-001"
    new_version = await store.append(stream_id, [_event(1)], expected_version=-1)
    assert new_version == 1


@pytest.mark.asyncio
async def test_append_existing_stream(store):
    stream_id = "test-exist-001"
    await store.append(stream_id, [_event(1)], expected_version=-1)
    new_version = await store.append(stream_id, [_event(2)], expected_version=1)
    assert new_version == 2


@pytest.mark.asyncio
async def test_occ_wrong_version_raises(store):
    stream_id = "test-occ-001"
    await store.append(stream_id, [_event(1)], expected_version=-1)
    with pytest.raises(OptimisticConcurrencyError) as exc:
        await store.append(stream_id, [_event(2)], expected_version=99)
    assert exc.value.expected_version == 99
    assert exc.value.actual_version == 1


@pytest.mark.asyncio
async def test_concurrent_double_append_exactly_one_succeeds(store):
    stream_id = "test-concurrent-001"
    await store.append(stream_id, [_event(0)], expected_version=-1)

    async def attempt(seq: int):
        return await store.append(stream_id, [_event(seq)], expected_version=1)

    results = await asyncio.gather(attempt(1), attempt(2), return_exceptions=True)
    successes = [r for r in results if isinstance(r, int)]
    errors = [r for r in results if isinstance(r, OptimisticConcurrencyError)]

    assert len(successes) == 1
    assert successes[0] == 2
    assert len(errors) == 1


@pytest.mark.asyncio
async def test_load_stream_ordered(store):
    stream_id = "test-load-001"
    await store.append(stream_id, [_event(1), _event(2), _event(3)], expected_version=-1)
    events = await store.load_stream(stream_id)
    assert len(events) == 3
    assert [e.stream_position for e in events] == [1, 2, 3]


@pytest.mark.asyncio
async def test_stream_version(store):
    stream_id = "test-ver-001"
    await store.append(stream_id, [_event(1), _event(2), _event(3), _event(4)], expected_version=-1)
    assert await store.stream_version(stream_id) == 4


@pytest.mark.asyncio
async def test_stream_version_nonexistent_is_zero_in_current_impl(store):
    assert await store.stream_version("test-does-not-exist") == 0


@pytest.mark.asyncio
async def test_load_all_yields_in_global_order(store):
    # Use distinct stream names to avoid inter-test overlap.
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    stream_a = f"test-global-A-{ts}"
    stream_b = f"test-global-B-{ts}"
    await store.append(stream_a, [_event(1), _event(2)], expected_version=-1)
    await store.append(stream_b, [_event(3), _event(4)], expected_version=-1)
    all_events = [e async for e in store.load_all(from_global_position=0)]
    positions = [e.global_position for e in all_events]
    assert positions == sorted(positions)
