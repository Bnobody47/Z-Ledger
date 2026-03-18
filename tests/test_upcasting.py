"""
Immutability test: v1 event stored, loaded as v2 via upcaster, raw DB payload confirmed unchanged.
"""
import pytest


@pytest.mark.asyncio
async def test_upcasting_immutability():
    """
    1. Directly query events table to get raw stored payload of a v1 event
    2. Load same event through EventStore.load_stream() and verify it is upcasted to v2
    3. Directly query events table again and verify raw stored payload is UNCHANGED
    """
    raise NotImplementedError
