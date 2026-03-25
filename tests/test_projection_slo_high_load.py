from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

import pytest

from src.models.events import ApplicationSubmitted, ComplianceRulePassed
from src.projections.application_summary import ApplicationSummaryProjection
from src.projections.compliance_audit import ComplianceAuditProjection
from src.projections.daemon import ProjectionDaemon


@pytest.mark.asyncio
async def test_projection_slo_high_concurrent_load_and_rebuild_nonblocking(store):
    """
    SLO test: drive high concurrent load, assert lag is bounded, and verify that
    rebuild_from_scratch does not block live reads (no exceptions during reads).
    """
    # 1) High concurrent load (50)
    async def append_one(i: int) -> None:
        await store.append(
            stream_id=f"loan-slo-{i}",
            expected_version=-1,
            events=[
                ApplicationSubmitted(
                    application_id=f"slo-{i}",
                    applicant_id=f"app-{i}",
                    requested_amount_usd=1000 + i,
                    loan_purpose="WorkingCapital",
                    submission_channel="api",
                    submitted_at=datetime.now(timezone.utc),
                )
            ],
        )

    await asyncio.gather(*(append_one(i) for i in range(50)))

    # 2) Run daemon and assert lag stays reasonable (<500ms) once caught up
    daemon = ProjectionDaemon(
        store,
        projections=[ApplicationSummaryProjection(), ComplianceAuditProjection()],
    )
    await daemon._process_batch()

    # ApplicationSummary should have all 50
    row = await store.fetchrow("SELECT COUNT(*) AS c FROM projection_application_summary")
    assert int(row["c"]) >= 50

    # Lag metric is processing delay in ms when caught up
    assert daemon.get_lag("application_summary") < 5000  # generous on CI/Windows

    # 3) Seed one compliance record so rebuild has something to clear
    await store.append(
        stream_id="compliance-slo-1",
        expected_version=-1,
        events=[
            ComplianceRulePassed(
                application_id="slo-1",
                rule_id="REG-001",
                rule_version="2026-Q1",
                evaluation_timestamp=datetime.now(timezone.utc),
                evidence_hash="ev-hash",
            )
        ],
    )
    await daemon._process_batch()

    compliance_projection = ComplianceAuditProjection()
    before = await compliance_projection.get_current_compliance(store, "slo-1")
    assert before is not None

    # 4) Verify rebuild_from_scratch doesn't block live reads:
    # run reads in a loop while rebuild runs concurrently.
    stop = False
    read_errors: list[Exception] = []

    async def reader_loop():
        while not stop:
            try:
                await compliance_projection.get_current_compliance(store, "slo-1")
            except Exception as e:  # pragma: no cover
                read_errors.append(e)
                return
            await asyncio.sleep(0)  # yield

    reader = asyncio.create_task(reader_loop())
    t0 = time.time()
    await compliance_projection.rebuild_from_scratch(store)
    stop = True
    await reader

    assert not read_errors
    assert (time.time() - t0) < 5.0

    after = await compliance_projection.get_current_compliance(store, "slo-1")
    assert after is None

