"""
ComplianceAuditView projection: temporal query support (get_compliance_at),
snapshot strategy, rebuild_from_scratch(). SLO: lag < 2s.
"""
from __future__ import annotations

import json

from src.projections.daemon import Projection


class ComplianceAuditProjection(Projection):
    name = "compliance_audit"

    async def handle(self, event, store) -> None:
        if not event.stream_id.startswith("compliance-"):
            return
        application_id = event.payload.get("application_id") or event.stream_id.replace("compliance-", "")

        # Build a single check entry for the incoming event.
        new_check: dict | None = None
        if event.event_type == "ComplianceRulePassed":
            new_check = {"rule_id": event.payload.get("rule_id"), "status": "PASSED"}
        elif event.event_type == "ComplianceRuleFailed":
            new_check = {"rule_id": event.payload.get("rule_id"), "status": "FAILED"}
        elif event.event_type == "ComplianceCheckRequested":
            new_check = {"required": event.payload.get("checks_required", [])}

        if new_check is None:
            return

        # Accumulate checks so the compliance resource can display the full set
        # of compliance outcomes across the application lifecycle.
        prev = await store.fetchrow(
            """
            SELECT checks, compliance_status
            FROM projection_compliance_audit
            WHERE application_id = $1
            ORDER BY as_of DESC
            LIMIT 1
            """,
            application_id,
        )

        prev_checks: list[dict] = []
        prev_status = "IN_PROGRESS"
        if prev:
            prev_status = prev["compliance_status"] or prev_status
            prev_checks_val = prev["checks"]
            if isinstance(prev_checks_val, str):
                prev_checks = json.loads(prev_checks_val)
            elif isinstance(prev_checks_val, list):
                prev_checks = prev_checks_val

        checks = prev_checks + [new_check]
        status = "FAILED" if new_check.get("status") == "FAILED" else prev_status
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
