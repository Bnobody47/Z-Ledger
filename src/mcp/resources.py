"""
6 MCP resources (query side): ledger://applications/{id},
ledger://applications/{id}/compliance, ledger://applications/{id}/audit-trail,
ledger://agents/{id}/performance, ledger://agents/{id}/sessions/{session_id},
ledger://ledger/health. All reading from projections.
"""
from __future__ import annotations

from datetime import datetime

from src.projections.compliance_audit import ComplianceAuditProjection


def register_resources(mcp, store, daemon) -> None:
    compliance_projection = ComplianceAuditProjection()

    @mcp.resource("ledger://applications/{id}")
    async def application_summary(id: str):  # noqa: A002
        row = await store.fetchrow(
            "SELECT * FROM projection_application_summary WHERE application_id = $1",
            id,
        )
        return dict(row) if row else {}

    @mcp.resource("ledger://applications/{id}/compliance")
    async def application_compliance(id: str, as_of: str | None = None):  # noqa: A002
        if as_of:
            return await compliance_projection.get_compliance_at(store, id, datetime.fromisoformat(as_of))
        return await compliance_projection.get_current_compliance(store, id)

    @mcp.resource("ledger://applications/{id}/audit-trail")
    async def application_audit_trail(id: str):  # noqa: A002
        events = await store.load_stream(f"audit-loan-{id}")
        return [{"event_type": e.event_type, "payload": e.payload} for e in events]

    @mcp.resource("ledger://agents/{id}/performance")
    async def agent_performance(id: str):  # noqa: A002
        rows = await store.fetch(
            "SELECT * FROM projection_agent_performance WHERE agent_id = $1 ORDER BY last_seen_at DESC",
            id,
        )
        return [dict(r) for r in rows]

    @mcp.resource("ledger://agents/{id}/sessions/{session_id}")
    async def agent_session(id: str, session_id: str):  # noqa: A002
        events = await store.load_stream(f"agent-{id}-{session_id}")
        return [{"event_type": e.event_type, "payload": e.payload} for e in events]

    @mcp.resource("ledger://ledger/health")
    async def ledger_health():
        return {
            "lags": {
                "application_summary": daemon.get_lag("application_summary"),
                "agent_performance": daemon.get_lag("agent_performance"),
                "compliance_audit": daemon.get_lag("compliance_audit"),
            }
        }
