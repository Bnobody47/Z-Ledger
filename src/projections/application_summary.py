"""
ApplicationSummary projection: one row per application, current state.
SLO: lag < 500ms.
"""
from src.projections.daemon import Projection


class ApplicationSummaryProjection(Projection):
    name = "application_summary"

    async def handle(self, event, store) -> None:
        application_id = event.payload.get("application_id")
        if not application_id:
            return
        if event.event_type == "ApplicationSubmitted":
            await store.execute(
                """
                INSERT INTO projection_application_summary (
                    application_id, state, applicant_id, requested_amount_usd, last_event_type, last_event_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (application_id)
                DO UPDATE SET state = EXCLUDED.state,
                              applicant_id = EXCLUDED.applicant_id,
                              requested_amount_usd = EXCLUDED.requested_amount_usd,
                              last_event_type = EXCLUDED.last_event_type,
                              last_event_at = EXCLUDED.last_event_at
                """,
                application_id,
                "SUBMITTED",
                event.payload.get("applicant_id"),
                event.payload.get("requested_amount_usd"),
                event.event_type,
                event.recorded_at,
            )
            return

        if event.event_type == "CreditAnalysisCompleted":
            await store.execute(
                """
                UPDATE projection_application_summary
                SET state = 'ANALYSIS_COMPLETE',
                    risk_tier = $2,
                    last_event_type = $3,
                    last_event_at = $4,
                    agent_sessions_completed = array_append(agent_sessions_completed, $5)
                WHERE application_id = $1
                """,
                application_id,
                event.payload.get("risk_tier"),
                event.event_type,
                event.recorded_at,
                f"agent-{event.payload.get('agent_id')}-{event.payload.get('session_id')}",
            )
            return

        if event.event_type == "ApplicationApproved":
            await store.execute(
                """
                UPDATE projection_application_summary
                SET state = 'FINAL_APPROVED',
                    approved_amount_usd = $2,
                    decision = 'APPROVE',
                    final_decision_at = $3,
                    last_event_type = $4,
                    last_event_at = $3
                WHERE application_id = $1
                """,
                application_id,
                event.payload.get("approved_amount_usd"),
                event.recorded_at,
                event.event_type,
            )
