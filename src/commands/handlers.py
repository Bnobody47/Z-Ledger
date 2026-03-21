"""Interim command handlers for submit + session start + credit analysis complete."""
from __future__ import annotations

from datetime import datetime, timezone

from src.models.events import (
    AgentContextLoaded,
    ApplicationSubmitted,
    ComplianceRuleFailed,
    ComplianceRulePassed,
    CreditAnalysisCompleted,
    DecisionGenerated,
    DomainError,
    FraudScreeningCompleted,
    HumanReviewCompleted,
)
from src.event_store import EventStore
from src.aggregates.loan_application import LoanApplicationAggregate
from src.aggregates.agent_session import AgentSessionAggregate


async def handle_submit_application(cmd: dict, store: EventStore) -> None:
    """Submit a new loan application to loan-{application_id}."""
    application_id = cmd["application_id"]
    stream_id = f"loan-{application_id}"
    app = await LoanApplicationAggregate.load(store, application_id)
    app.assert_can_submit()

    event = ApplicationSubmitted(
        application_id=application_id,
        applicant_id=cmd["applicant_id"],
        requested_amount_usd=float(cmd["requested_amount_usd"]),
        loan_purpose=cmd.get("loan_purpose", "UNKNOWN"),
        submission_channel=cmd.get("submission_channel", "api"),
        submitted_at=cmd.get("submitted_at", datetime.now(timezone.utc)),
    )
    await store.append(
        stream_id=stream_id,
        events=[event],
        expected_version=app.version - 1,
        correlation_id=cmd.get("correlation_id"),
        causation_id=cmd.get("causation_id"),
    )


async def handle_credit_analysis_completed(cmd: dict, store: EventStore) -> None:
    """Record CreditAnalysisCompleted. Requires active AgentSession with context loaded."""
    app = await LoanApplicationAggregate.load(store, cmd["application_id"])
    agent = await AgentSessionAggregate.load(store, cmd["agent_id"], cmd["session_id"])
    app.assert_awaiting_credit_analysis()
    agent.assert_context_loaded()
    agent.assert_model_version_current(cmd["model_version"])

    event = CreditAnalysisCompleted(
        application_id=cmd["application_id"],
        agent_id=cmd["agent_id"],
        session_id=cmd["session_id"],
        model_version=cmd["model_version"],
        confidence_score=float(cmd["confidence_score"]),
        risk_tier=cmd["risk_tier"],
        recommended_limit_usd=float(cmd["recommended_limit_usd"]),
        analysis_duration_ms=int(cmd.get("analysis_duration_ms", 0)),
        input_data_hash=cmd.get("input_data_hash", "unknown"),
    )
    await store.append(
        stream_id=f"loan-{cmd['application_id']}",
        events=[event],
        expected_version=app.version,
        correlation_id=cmd.get("correlation_id"),
        causation_id=cmd.get("causation_id"),
    )


async def handle_fraud_screening_completed(cmd: dict, store: EventStore) -> None:
    """Record FraudScreeningCompleted."""
    app = await LoanApplicationAggregate.load(store, cmd["application_id"])
    app.assert_not_terminal()
    event = FraudScreeningCompleted(
        application_id=cmd["application_id"],
        agent_id=cmd["agent_id"],
        fraud_score=float(cmd["fraud_score"]),
        anomaly_flags=cmd.get("anomaly_flags", []),
        screening_model_version=cmd.get("screening_model_version", "unknown"),
        input_data_hash=cmd.get("input_data_hash", "unknown"),
    )
    await store.append(
        stream_id=f"loan-{cmd['application_id']}",
        events=[event],
        expected_version=app.version,
    )


async def handle_compliance_check(cmd: dict, store: EventStore) -> None:
    """Record ComplianceRulePassed or ComplianceRuleFailed."""
    stream_id = f"compliance-{cmd['application_id']}"
    version = await store.stream_version(stream_id)
    if cmd.get("passed", True):
        event = ComplianceRulePassed(
            application_id=cmd["application_id"],
            rule_id=cmd["rule_id"],
            rule_version=cmd.get("rule_version", "2026-Q1"),
            evaluation_timestamp=cmd.get("evaluation_timestamp", datetime.now(timezone.utc)),
            evidence_hash=cmd.get("evidence_hash", "unknown"),
        )
    else:
        event = ComplianceRuleFailed(
            application_id=cmd["application_id"],
            rule_id=cmd["rule_id"],
            rule_version=cmd.get("rule_version", "2026-Q1"),
            failure_reason=cmd.get("failure_reason", "RULE_FAILED"),
            remediation_required=bool(cmd.get("remediation_required", False)),
        )
    await store.append(
        stream_id=stream_id,
        events=[event],
        expected_version=-1 if version == 0 else version,
    )


async def handle_generate_decision(cmd: dict, store: EventStore) -> None:
    """Generate DecisionGenerated. All required analyses must be present."""
    app = await LoanApplicationAggregate.load(store, cmd["application_id"])
    app.assert_not_terminal()
    recommendation = cmd["recommendation"]
    confidence_score = float(cmd["confidence_score"])
    if confidence_score < 0.6:
        recommendation = "REFER"
    event = DecisionGenerated(
        application_id=cmd["application_id"],
        orchestrator_agent_id=cmd["orchestrator_agent_id"],
        recommendation=recommendation,
        confidence_score=confidence_score,
        contributing_agent_sessions=cmd.get("contributing_agent_sessions", []),
        decision_basis_summary=cmd.get("decision_basis_summary", ""),
        model_versions=cmd.get("model_versions", {}),
    )
    await store.append(
        stream_id=f"loan-{cmd['application_id']}",
        events=[event],
        expected_version=app.version,
    )


async def handle_human_review_completed(cmd: dict, store: EventStore) -> None:
    """Record HumanReviewCompleted."""
    app = await LoanApplicationAggregate.load(store, cmd["application_id"])
    app.assert_not_terminal()
    if cmd.get("override") and not cmd.get("override_reason"):
        raise DomainError("override_reason is required when override=True")
    event = HumanReviewCompleted(
        application_id=cmd["application_id"],
        reviewer_id=cmd["reviewer_id"],
        override=bool(cmd.get("override", False)),
        final_decision=cmd["final_decision"],
        override_reason=cmd.get("override_reason"),
    )
    await store.append(
        stream_id=f"loan-{cmd['application_id']}",
        events=[event],
        expected_version=app.version,
    )


async def handle_start_agent_session(cmd: dict, store: EventStore) -> None:
    """Start agent session (AgentContextLoaded). Gas Town: required before any agent decision."""
    stream_id = f"agent-{cmd['agent_id']}-{cmd['session_id']}"
    event = AgentContextLoaded(
        agent_id=cmd["agent_id"],
        session_id=cmd["session_id"],
        context_source=cmd.get("context_source", "fresh"),
        event_replay_from_position=int(cmd.get("event_replay_from_position", 0)),
        context_token_count=int(cmd.get("context_token_count", 0)),
        model_version=cmd["model_version"],
    )
    await store.append(stream_id=stream_id, events=[event], expected_version=-1)
