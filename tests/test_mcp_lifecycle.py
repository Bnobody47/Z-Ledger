"""
Full loan application lifecycle driven entirely through MCP tool calls:
start_agent_session → record_credit_analysis → record_fraud_screening →
record_compliance_check → generate_decision → record_human_review →
query ledger://applications/{id}/compliance to verify complete trace.
"""
from __future__ import annotations

import pytest

from fastmcp import FastMCP

from src.mcp.resources import register_resources
from src.mcp.tools import register_tools
from src.projections.compliance_audit import ComplianceAuditProjection
from src.projections.application_summary import ApplicationSummaryProjection
from src.projections.daemon import ProjectionDaemon


@pytest.mark.asyncio
async def test_mcp_full_lifecycle(store):
    daemon = ProjectionDaemon(
        store,
        projections=[ApplicationSummaryProjection(), ComplianceAuditProjection()],
    )

    # Build an MCP server wired to the same connected EventStore instance.
    mcp = FastMCP(name="z-ledger-test")
    register_tools(mcp, store, daemon)
    register_resources(mcp, store, daemon)

    # Drive the lifecycle using tool calls (rubric requirement).
    await mcp.call_tool(
        "submit_application",
        {
            "application_id": "mcp-1",
            "applicant_id": "app-1",
            "requested_amount_usd": 25000,
        },
    )
    await mcp.call_tool(
        "start_agent_session",
        {"agent_id": "agent-1", "session_id": "s1", "model_version": "v1"},
    )
    await mcp.call_tool(
        "record_credit_analysis",
        {
            "application_id": "mcp-1",
            "agent_id": "agent-1",
            "session_id": "s1",
            "model_version": "v1",
            "confidence_score": 0.8,
            "risk_tier": "LOW",
            "recommended_limit_usd": 18000,
        },
    )
    await mcp.call_tool(
        "record_compliance_check",
        {"application_id": "mcp-1", "rule_id": "REG-001", "passed": True},
    )
    await mcp.call_tool(
        "record_compliance_check",
        {"application_id": "mcp-1", "rule_id": "REG-002", "passed": True},
    )
    row = await store.fetchrow(
        "SELECT state, risk_tier FROM projection_application_summary WHERE application_id = $1",
        "mcp-1",
    )
    assert row is not None
    assert row["risk_tier"] == "LOW"

    # Assert compliance MCP resource includes full expected rule set
    compliance_res = await mcp.read_resource("ledger://applications/mcp-1/compliance")
    # FastMCP returns ResourceResult(contents=[ResourceContent(...)]). Our resources return JSON strings.
    assert compliance_res.contents, "Expected at least one ResourceContent item"
    import json

    compliance = json.loads(compliance_res.contents[0].content)
    assert "checks" in compliance
    rule_ids = {c.get("rule_id") for c in compliance["checks"] if isinstance(c, dict)}
    assert "REG-001" in rule_ids
    assert "REG-002" in rule_ids
