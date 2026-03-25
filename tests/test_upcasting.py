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
    # v2 view shape assertions
    assert credit_event.payload["model_version"] == "legacy-pre-2026"
    assert "confidence_score" in credit_event.payload
    assert "regulatory_basis" in credit_event.payload
    assert raw_before["payload"] == raw_after["payload"]


@pytest.mark.asyncio
async def test_upcasting_decision_infers_model_versions(store):
    stream_id = "loan-upcast-decision-1"
    await store.append(
        stream_id=stream_id,
        expected_version=-1,
        events=[
            ApplicationSubmitted(
                application_id="upcast-decision-1",
                applicant_id="app-1",
                requested_amount_usd=1000,
                loan_purpose="Ops",
                submission_channel="api",
                submitted_at=datetime.now(timezone.utc),
            )
        ],
    )
    await store.execute("UPDATE event_streams SET current_version = 1 WHERE stream_id = $1", stream_id)

    v1_payload = {
        "application_id": "upcast-decision-1",
        "orchestrator_agent_id": "orch-1",
        "recommendation": "REFER",
        "confidence_score": 0.55,
        "contributing_agent_sessions": ["agent-agentA-s1", "agent-agentB-s2"],
        "decision_basis_summary": "basis",
    }
    await store.execute(
        """
        INSERT INTO events (stream_id, stream_position, event_type, event_version, payload, metadata)
        VALUES ($1, 2, 'DecisionGenerated', 1, $2::jsonb, '{}'::jsonb)
        """,
        stream_id,
        v1_payload,
    )
    await store.execute("UPDATE event_streams SET current_version = 2 WHERE stream_id = $1", stream_id)

    raw_before = await store.fetchrow(
        "SELECT payload, event_version FROM events WHERE stream_id = $1 AND stream_position = 2",
        stream_id,
    )
    loaded = await store.load_stream(stream_id)
    decision_event = loaded[-1]
    raw_after = await store.fetchrow(
        "SELECT payload, event_version FROM events WHERE stream_id = $1 AND stream_position = 2",
        stream_id,
    )

    assert raw_before["event_version"] == 1
    assert decision_event.event_version == 2
    assert "model_versions" in decision_event.payload
    assert decision_event.payload["model_versions"].get("agentA") == "inferred-from-session"
    assert decision_event.payload["model_versions"].get("agentB") == "inferred-from-session"
    # Raw row must remain v1
    assert raw_before["payload"] == raw_after["payload"]
