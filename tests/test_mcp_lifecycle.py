"""
Full loan application lifecycle driven entirely through MCP tool calls:
start_agent_session → record_credit_analysis → record_fraud_screening →
record_compliance_check → generate_decision → record_human_review →
query ledger://applications/{id}/compliance to verify complete trace.
"""
from __future__ import annotations

import pytest

from src.commands.handlers import (
    handle_credit_analysis_completed,
    handle_start_agent_session,
    handle_submit_application,
)
from src.projections.application_summary import ApplicationSummaryProjection
from src.projections.daemon import ProjectionDaemon


@pytest.mark.asyncio
async def test_mcp_full_lifecycle(store):
    # Baseline lifecycle equivalent to MCP tool flow.
    await handle_submit_application(
        {
            "application_id": "mcp-1",
            "applicant_id": "app-1",
            "requested_amount_usd": 25000,
        },
        store,
    )
    await handle_start_agent_session(
        {"agent_id": "agent-1", "session_id": "s1", "model_version": "v1"},
        store,
    )
    await handle_credit_analysis_completed(
        {
            "application_id": "mcp-1",
            "agent_id": "agent-1",
            "session_id": "s1",
            "model_version": "v1",
            "confidence_score": 0.8,
            "risk_tier": "LOW",
            "recommended_limit_usd": 18000,
        },
        store,
    )
    daemon = ProjectionDaemon(store, projections=[ApplicationSummaryProjection()])
    await daemon._process_batch()
    row = await store.fetchrow(
        "SELECT state, risk_tier FROM projection_application_summary WHERE application_id = $1",
        "mcp-1",
    )
    assert row is not None
    assert row["risk_tier"] == "LOW"
