"""Projection daemon + read model tests."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from src.models.events import ApplicationSubmitted, ComplianceRulePassed
from src.projections.agent_performance import AgentPerformanceProjection
from src.projections.application_summary import ApplicationSummaryProjection
from src.projections.compliance_audit import ComplianceAuditProjection
from src.projections.daemon import ProjectionDaemon


@pytest.mark.asyncio
async def test_projection_lag_slo(store):
    async def append_one(i: int) -> None:
        await store.append(
            stream_id=f"loan-proj-{i}",
            expected_version=-1,
            events=[
                ApplicationSubmitted(
                    application_id=f"proj-{i}",
                    applicant_id=f"app-{i}",
                    requested_amount_usd=1000 + i,
                    loan_purpose="WorkingCapital",
                    submission_channel="api",
                    submitted_at=datetime.now(timezone.utc),
                )
            ],
        )

    await asyncio.gather(*(append_one(i) for i in range(20)))
    daemon = ProjectionDaemon(
        store,
        projections=[
            ApplicationSummaryProjection(),
            AgentPerformanceProjection(),
            ComplianceAuditProjection(),
        ],
    )
    await daemon._process_batch()
    row = await store.fetchrow("SELECT COUNT(*) AS c FROM projection_application_summary")
    assert int(row["c"]) >= 20
    assert daemon.get_lag("application_summary") >= 0


@pytest.mark.asyncio
async def test_rebuild_from_scratch(store):
    projection = ComplianceAuditProjection()
    await store.append(
        stream_id="compliance-proj-1",
        expected_version=-1,
        events=[
            ComplianceRulePassed(
                application_id="proj-1",
                rule_id="REG-001",
                rule_version="2026-Q1",
                evaluation_timestamp=datetime.now(timezone.utc),
                evidence_hash="ev-hash",
            )
        ],
    )
    daemon = ProjectionDaemon(store, projections=[projection])
    await daemon._process_batch()
    before = await projection.get_current_compliance(store, "proj-1")
    assert before is not None
    await projection.rebuild_from_scratch(store)
    after = await projection.get_current_compliance(store, "proj-1")
    assert after is None
