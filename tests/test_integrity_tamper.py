"""Audit integrity chain tamper detection tests."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.event_store import EventStore
from src.integrity.audit_chain import run_integrity_check
from src.models.events import ApplicationSubmitted


@pytest.mark.asyncio
async def test_integrity_check_detects_tamper(store):
    # Use the primary stream scheme used by the code: loan-{application_id}
    entity_type = "loan"
    entity_id = "integrity-1"
    primary_stream = f"{entity_type}-{entity_id}"

    await store.append(
        stream_id=primary_stream,
        expected_version=-1,
        events=[
            ApplicationSubmitted(
                application_id=entity_id,
                applicant_id="app-1",
                requested_amount_usd=1000,
                loan_purpose="WorkingCapital",
                submission_channel="api",
                submitted_at=datetime.now(timezone.utc),
            )
        ],
    )

    first = await run_integrity_check(store, entity_type, entity_id)
    assert first["tamper_detected"] is False
    assert first["chain_valid"] is True

    # Tamper with stored payload in-place.
    await store.execute(
        """
        UPDATE events
        SET payload = jsonb_set(payload, '{requested_amount_usd}', '999'::jsonb, true)
        WHERE stream_id = $1 AND event_type = 'ApplicationSubmitted'
        """,
        primary_stream,
    )

    second = await run_integrity_check(store, entity_type, entity_id)
    assert second["tamper_detected"] is True

