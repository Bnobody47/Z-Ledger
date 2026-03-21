"""
Immutability test: v1 event stored, loaded as v2 via upcaster, raw DB payload confirmed unchanged.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.models.events import ApplicationSubmitted


@pytest.mark.asyncio
async def test_upcasting_immutability(store):
    stream_id = "loan-upcast-1"
    await store.append(
        stream_id=stream_id,
        expected_version=-1,
        events=[
            ApplicationSubmitted(
                application_id="upcast-1",
                applicant_id="app-1",
                requested_amount_usd=1000,
                loan_purpose="Ops",
                submission_channel="api",
                submitted_at=datetime.now(timezone.utc),
            )
        ],
    )
    # Insert v1 credit event directly (without v2 fields), mimicking historical data.
    await store.execute(
        """
        UPDATE event_streams SET current_version = 1 WHERE stream_id = $1
        """,
        stream_id,
    )
    await store.execute(
        """
        INSERT INTO events (stream_id, stream_position, event_type, event_version, payload, metadata)
        VALUES ($1, 2, 'CreditAnalysisCompleted', 1, $2::jsonb, '{}'::jsonb)
        """,
        stream_id,
        {
            "application_id": "upcast-1",
            "agent_id": "agent-1",
            "session_id": "s-1",
            "risk_tier": "LOW",
            "recommended_limit_usd": 500,
            "analysis_duration_ms": 10,
            "input_data_hash": "h1",
        },
    )
    await store.execute(
        "UPDATE event_streams SET current_version = 2 WHERE stream_id = $1",
        stream_id,
    )

    raw_before = await store.fetchrow(
        """
        SELECT payload, event_version FROM events
        WHERE stream_id = $1 AND stream_position = 2
        """,
        stream_id,
    )
    loaded = await store.load_stream(stream_id)
    credit_event = loaded[-1]
    raw_after = await store.fetchrow(
        """
        SELECT payload, event_version FROM events
        WHERE stream_id = $1 AND stream_position = 2
        """,
        stream_id,
    )

    assert raw_before["event_version"] == 1
    assert credit_event.event_version == 2
    assert "model_version" in credit_event.payload
    assert raw_before["payload"] == raw_after["payload"]
