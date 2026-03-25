"""
8 MCP tools (command side): submit_application, record_credit_analysis,
record_fraud_screening, record_compliance_check, generate_decision,
record_human_review, start_agent_session, run_integrity_check.
All with structured error types and precondition documentation.
"""
from __future__ import annotations

from datetime import datetime, timezone

from src.commands.handlers import (
    handle_compliance_check,
    handle_credit_analysis_completed,
    handle_fraud_screening_completed,
    handle_generate_decision,
    handle_human_review_completed,
    handle_start_agent_session,
    handle_submit_application,
)
from src.integrity.audit_chain import run_integrity_check as run_integrity_check_impl
from src.models.events import DomainError, OptimisticConcurrencyError


def _structured_error(exc: Exception) -> dict:
    if isinstance(exc, OptimisticConcurrencyError):
        return {
            "error_type": "OptimisticConcurrencyError",
            "message": str(exc),
            "context": {
                "stream_id": exc.stream_id,
                "expected_version": exc.expected_version,
                "actual_version": exc.actual_version,
            },
            "suggested_action": "reload_stream_and_retry",
        }
    if isinstance(exc, DomainError):
        return {
            "error_type": "DomainError",
            "message": str(exc),
            "context": {},
            "suggested_action": "fix_preconditions_and_retry",
        }
    return {
        "error_type": type(exc).__name__,
        "message": str(exc),
        "context": {},
        "suggested_action": "review_input_and_retry",
    }


def register_tools(mcp, store) -> None:
    @mcp.tool(
        description=(
            "Submit a new application. Preconditions: application_id must be unique. "
            "Returns stream_id and initial_version."
        )
    )
    async def submit_application(application_id: str, applicant_id: str, requested_amount_usd: float):
        try:
            await handle_submit_application(
                {
                    "application_id": application_id,
                    "applicant_id": applicant_id,
                    "requested_amount_usd": requested_amount_usd,
                    "loan_purpose": "WorkingCapital",
                    "submission_channel": "mcp",
                    "submitted_at": datetime.now(timezone.utc),
                },
                store,
            )
            return {"stream_id": f"loan-{application_id}", "initial_version": 1}
        except Exception as exc:  # pragma: no cover
            return _structured_error(exc)

    @mcp.tool(
        description=(
            "Start agent session. Preconditions: call before any decision tools. "
            "Writes AgentContextLoaded event."
        )
    )
    async def start_agent_session(agent_id: str, session_id: str, model_version: str):
        try:
            await handle_start_agent_session(
                {
                    "agent_id": agent_id,
                    "session_id": session_id,
                    "model_version": model_version,
                    "context_source": "fresh",
                    "event_replay_from_position": 0,
                    "context_token_count": 0,
                },
                store,
            )
            return {"session_id": session_id, "context_position": 1}
        except Exception as exc:  # pragma: no cover
            return _structured_error(exc)

    @mcp.tool(
        description=(
            "Record credit analysis. Preconditions: active session via start_agent_session. "
            "Optimistic concurrency enforced on loan stream."
        )
    )
    async def record_credit_analysis(
        application_id: str,
        agent_id: str,
        session_id: str,
        model_version: str,
        confidence_score: float,
        risk_tier: str,
        recommended_limit_usd: float,
    ):
        try:
            await handle_credit_analysis_completed(
                {
                    "application_id": application_id,
                    "agent_id": agent_id,
                    "session_id": session_id,
                    "model_version": model_version,
                    "confidence_score": confidence_score,
                    "risk_tier": risk_tier,
                    "recommended_limit_usd": recommended_limit_usd,
                    "analysis_duration_ms": 100,
                    "input_data_hash": "mcp-input-hash",
                },
                store,
            )
            return {"event_type": "CreditAnalysisCompleted"}
        except Exception as exc:  # pragma: no cover
            return _structured_error(exc)

    @mcp.tool(description="Record fraud screening.")
    async def record_fraud_screening(
        application_id: str, agent_id: str, fraud_score: float, anomaly_flags: list[str] | None = None
    ):
        try:
            await handle_fraud_screening_completed(
                {
                    "application_id": application_id,
                    "agent_id": agent_id,
                    "fraud_score": fraud_score,
                    "anomaly_flags": anomaly_flags or [],
                    "screening_model_version": "fraud-v1",
                },
                store,
            )
            return {"event_type": "FraudScreeningCompleted"}
        except Exception as exc:  # pragma: no cover
            return _structured_error(exc)

    @mcp.tool(description="Record compliance check.")
    async def record_compliance_check(application_id: str, rule_id: str, passed: bool):
        try:
            await handle_compliance_check(
                {"application_id": application_id, "rule_id": rule_id, "passed": passed},
                store,
            )
            return {"check_id": rule_id, "compliance_status": "PASSED" if passed else "FAILED"}
        except Exception as exc:  # pragma: no cover
            return _structured_error(exc)

    @mcp.tool(description="Generate decision with confidence-floor enforcement.")
    async def generate_decision(
        application_id: str, orchestrator_agent_id: str, recommendation: str, confidence_score: float
    ):
        try:
            await handle_generate_decision(
                {
                    "application_id": application_id,
                    "orchestrator_agent_id": orchestrator_agent_id,
                    "recommendation": recommendation,
                    "confidence_score": confidence_score,
                },
                store,
            )
            return {"decision_id": application_id, "recommendation": recommendation}
        except Exception as exc:  # pragma: no cover
            return _structured_error(exc)

    @mcp.tool(description="Record human review decision.")
    async def record_human_review(
        application_id: str, reviewer_id: str, final_decision: str, override: bool = False
    ):
        try:
            await handle_human_review_completed(
                {
                    "application_id": application_id,
                    "reviewer_id": reviewer_id,
                    "final_decision": final_decision,
                    "override": override,
                },
                store,
            )
            return {"final_decision": final_decision, "application_state": "REVIEWED"}
        except Exception as exc:  # pragma: no cover
            return _structured_error(exc)

    @mcp.tool(description="Run audit chain integrity check for an entity.")
    async def run_integrity_check(entity_type: str, entity_id: str):
        try:
            return await run_integrity_check_impl(store, entity_type, entity_id)
        except Exception as exc:  # pragma: no cover
            return _structured_error(exc)
