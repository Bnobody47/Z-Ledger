"""
Double-decision concurrency test: two concurrent asyncio tasks appending to the same
stream at expected_version=3. Asserts exactly one succeeds, one raises
OptimisticConcurrencyError, and total stream length = 4.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from src.models.events import (
    ApplicationSubmitted,
    CreditAnalysisCompleted,
    CreditAnalysisRequested,
    OptimisticConcurrencyError,
)


@pytest.mark.asyncio
async def test_double_decision_concurrency(store):
    """
    Two AI agents simultaneously attempt to append CreditAnalysisCompleted to the same
    loan application stream. Both read at version 3 and pass expected_version=3.
    Exactly one must succeed. The other must receive OptimisticConcurrencyError.
    Total events appended = 4 (not 5).
    """
    stream_id = "loan-app-concurrency-1"
    # Seed stream to version 3.
    await store.append(
        stream_id=stream_id,
        expected_version=-1,
        events=[
            ApplicationSubmitted(
                application_id="app-concurrency-1",
                applicant_id="applicant-1",
                requested_amount_usd=100000,
                loan_purpose="WorkingCapital",
                submission_channel="api",
                submitted_at=datetime.now(timezone.utc),
            ),
            CreditAnalysisRequested(
                application_id="app-concurrency-1",
                assigned_agent_id="agent-a",
                requested_at=datetime.now(timezone.utc),
                priority="HIGH",
            ),
            CreditAnalysisRequested(
                application_id="app-concurrency-1",
                assigned_agent_id="agent-b",
                requested_at=datetime.now(timezone.utc),
                priority="HIGH",
            ),
        ],
    )

    start = asyncio.Event()

    async def try_append(agent_id: str):
        await start.wait()
        return await store.append(
            stream_id=stream_id,
            expected_version=3,
            events=[
                CreditAnalysisCompleted(
                    application_id="app-concurrency-1",
                    agent_id=agent_id,
                    session_id=f"session-{agent_id}",
                    model_version="credit-v1",
                    confidence_score=0.83,
                    risk_tier="MEDIUM",
                    recommended_limit_usd=75000,
                    analysis_duration_ms=250,
                    input_data_hash=f"hash-{agent_id}",
                )
            ],
        )

    t1 = asyncio.create_task(try_append("agent-a"))
    t2 = asyncio.create_task(try_append("agent-b"))
    start.set()
    results = await asyncio.gather(t1, t2, return_exceptions=True)

    successes = [r for r in results if isinstance(r, int)]
    failures = [r for r in results if isinstance(r, Exception)]

    assert len(successes) == 1
    assert successes[0] == 4
    assert len(failures) == 1
    assert isinstance(failures[0], OptimisticConcurrencyError)

    stream_events = await store.load_stream(stream_id)
    assert len(stream_events) == 4
    assert stream_events[-1].stream_position == 4
