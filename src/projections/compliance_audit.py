"""
ComplianceAuditView projection: temporal query support (get_compliance_at),
snapshot strategy, rebuild_from_scratch(). SLO: lag < 2s.
"""
from __future__ import annotations

from src.projections.daemon import Projection


class ComplianceAuditProjection(Projection):
    name = "compliance_audit"

    async def handle(self, event, store) -> None:
        if not event.stream_id.startswith("compliance-"):
            return
        application_id = event.payload.get("application_id") or event.stream_id.replace("compliance-", "")
        checks = []
        status = "IN_PROGRESS"
        if event.event_type == "ComplianceRulePassed":
            checks = [{"rule_id": event.payload.get("rule_id"), "status": "PASSED"}]
        elif event.event_type == "ComplianceRuleFailed":
            checks = [{"rule_id": event.payload.get("rule_id"), "status": "FAILED"}]
            status = "FAILED"
        elif event.event_type == "ComplianceCheckRequested":
            checks = [{"required": event.payload.get("checks_required", [])}]
        await store.execute(
            """
            INSERT INTO projection_compliance_audit (
                application_id, as_of, compliance_status, checks, regulation_versions, last_event_type, last_event_at
            ) VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $2)
            """,
            application_id,
            event.recorded_at,
            status,
            checks,
            {"regulation_set_version": event.payload.get("regulation_set_version")},
            event.event_type,
        )

    async def get_current_compliance(self, store, application_id: str) -> dict | None:
        row = await store.fetchrow(
            """
            SELECT * FROM projection_compliance_audit
            WHERE application_id = $1
            ORDER BY as_of DESC
            LIMIT 1
            """,
            application_id,
        )
        return dict(row) if row else None

    async def get_compliance_at(self, store, application_id: str, timestamp) -> dict | None:
        row = await store.fetchrow(
            """
            SELECT * FROM projection_compliance_audit
            WHERE application_id = $1 AND as_of <= $2
            ORDER BY as_of DESC
            LIMIT 1
            """,
            application_id,
            timestamp,
        )
        return dict(row) if row else None

    async def rebuild_from_scratch(self, store) -> None:
        await store.execute("TRUNCATE TABLE projection_compliance_audit")
