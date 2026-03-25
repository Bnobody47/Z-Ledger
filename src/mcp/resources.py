"""
6 MCP resources (query side): ledger://applications/{id},
ledger://applications/{id}/compliance, ledger://applications/{id}/audit-trail,
ledger://agents/{id}/performance, ledger://agents/{id}/sessions/{session_id},
ledger://ledger/health. All reading from projections.
"""
from __future__ import annotations

import json
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
        return json.dumps(dict(row) if row else {}, default=str)

    @mcp.resource("ledger://applications/{id}/compliance")
    async def application_compliance(id: str, as_of: str | None = None):  # noqa: A002
        # This resource reads from the compliance projection table.
        # The projection daemon builds this read model by replaying
        # the compliance-{application_id} event stream (see ProjectionDaemon).
        if as_of:
            row = await compliance_projection.get_compliance_at(store, id, datetime.fromisoformat(as_of))
        else:
            row = await compliance_projection.get_current_compliance(store, id)
        if not row:
            return json.dumps({}, default=str)
        # asyncpg may return jsonb as a JSON string depending on codecs.
        if isinstance(row.get("checks"), str):
            row["checks"] = json.loads(row["checks"])
        return json.dumps(row, default=str)

    @mcp.resource("ledger://applications/{id}/audit-trail")
    async def application_audit_trail(id: str):  # noqa: A002
        # This endpoint is served directly from the audit ledger stream.
        # It uses `store.load_stream(...)` to replay the aggregate event history
        # and present the raw audit chain events to the consumer.
        events = await store.load_stream(f"audit-loan-{id}")
        return json.dumps(
            [{"event_type": e.event_type, "payload": e.payload} for e in events],
            default=str,
        )

    @mcp.resource("ledger://agents/{id}/performance")
    async def agent_performance(id: str):  # noqa: A002
        rows = await store.fetch(
            "SELECT * FROM projection_agent_performance WHERE agent_id = $1 ORDER BY last_seen_at DESC",
            id,
        )
        return json.dumps([dict(r) for r in rows], default=str)

    @mcp.resource("ledger://agents/{id}/sessions/{session_id}")
    async def agent_session(id: str, session_id: str):  # noqa: A002
        # This endpoint reads directly from the agent session stream.
        # It uses `store.load_stream(...)` to replay the session's events so
        # the LLM consumer can inspect what happened during the session.
        events = await store.load_stream(f"agent-{id}-{session_id}")
        return json.dumps(
            [{"event_type": e.event_type, "payload": e.payload} for e in events],
            default=str,
        )

    @mcp.resource("ledger://ledger/health")
    async def ledger_health():
        return json.dumps(
            {
            "lags": {
                "application_summary": daemon.get_lag("application_summary"),
                "agent_performance": daemon.get_lag("agent_performance"),
                "compliance_audit": daemon.get_lag("compliance_audit"),
            }
            },
            default=str,
        )
