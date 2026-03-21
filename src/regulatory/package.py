"""
generate_regulatory_package(): self-contained JSON examination package with
event stream, projection states at examination date, integrity verification,
human-readable narrative, and agent model metadata.
"""
from __future__ import annotations

from datetime import datetime

from src.event_store import EventStore
from src.integrity.audit_chain import run_integrity_check
from src.projections.compliance_audit import ComplianceAuditProjection


async def generate_regulatory_package(
    store: EventStore,
    application_id: str,
    examination_date: str,
) -> dict:
    """Produce complete, self-contained regulatory package."""
    as_of = datetime.fromisoformat(examination_date)
    loan_stream = await store.load_stream(f"loan-{application_id}")
    compliance_projection = ComplianceAuditProjection()
    compliance_state = await compliance_projection.get_compliance_at(store, application_id, as_of)
    integrity = await run_integrity_check(store, "loan", application_id)

    narrative = []
    for e in loan_stream:
        narrative.append(
            f"{e.recorded_at.isoformat()} - {e.event_type} (stream_position={e.stream_position})"
        )

    return {
        "application_id": application_id,
        "examination_date": examination_date,
        "event_stream": [
            {
                "event_id": str(e.event_id),
                "stream_position": e.stream_position,
                "event_type": e.event_type,
                "event_version": e.event_version,
                "payload": e.payload,
                "metadata": e.metadata,
                "recorded_at": e.recorded_at.isoformat(),
            }
            for e in loan_stream
        ],
        "projections": {
            "compliance_at_examination": compliance_state,
        },
        "integrity_verification": integrity,
        "narrative": narrative,
        "agent_metadata": [
            {
                "agent_id": e.payload.get("agent_id"),
                "model_version": e.payload.get("model_version"),
                "confidence_score": e.payload.get("confidence_score"),
                "input_data_hash": e.payload.get("input_data_hash"),
            }
            for e in loan_stream
            if e.event_type in {"CreditAnalysisCompleted", "FraudScreeningCompleted", "DecisionGenerated"}
        ],
    }
