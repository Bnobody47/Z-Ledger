from __future__ import annotations

import pytest
from datetime import datetime, timezone

from src.commands.handlers import (
    handle_generate_decision,
    handle_human_review_completed,
)
from src.models.events import (
    AgentContextLoaded,
    ApplicationSubmitted,
    ComplianceRuleFailed,
    ComplianceRulePassed,
    CreditAnalysisCompleted,
    DomainError,
)


@pytest.fixture
def _session_entry() -> str:
    # Matches LoanApplicationAggregate._parse_contributing_session format
    return "agent-agentA-s1"


async def _seed_agent_session(store, agent_id: str, session_id: str, model_version: str) -> None:
    await store.append(
        stream_id=f"agent-{agent_id}-{session_id}",
        expected_version=-1,
        events=[
            AgentContextLoaded(
                agent_id=agent_id,
                session_id=session_id,
                context_source="fresh",
                event_replay_from_position=0,
                context_token_count=0,
                model_version=model_version,
            )
        ],
    )


async def _seed_loan_after_credit(store, application_id: str, *, agent_id: str, session_id: str, model_version: str) -> None:
    # Loan aggregate state is derived purely from its own stream, so we seed with
    # a single CreditAnalysisCompleted to reach ANALYSIS_COMPLETE.
    await store.append(
        stream_id=f"loan-{application_id}",
        expected_version=-1,
        events=[
            CreditAnalysisCompleted(
                application_id=application_id,
                agent_id=agent_id,
                session_id=session_id,
                model_version=model_version,
                confidence_score=0.8,
                risk_tier="LOW",
                recommended_limit_usd=18000,
                analysis_duration_ms=250,
                input_data_hash="h1",
            )
        ],
    )


async def _seed_compliance_passed(store, application_id: str, rule_id: str = "REG-001") -> None:
    await store.append(
        stream_id=f"compliance-{application_id}",
        expected_version=-1,
        events=[
            ComplianceRulePassed(
                application_id=application_id,
                rule_id=rule_id,
                rule_version="2026-Q1",
                evaluation_timestamp=datetime.now(timezone.utc),
                evidence_hash="ev-hash",
            )
        ],
    )


async def _seed_compliance_hard_block(store, application_id: str, rule_id: str = "REG-003") -> None:
    await store.append(
        stream_id=f"compliance-{application_id}",
        expected_version=-1,
        events=[
            ComplianceRuleFailed(
                application_id=application_id,
                rule_id=rule_id,
                rule_version="2026-Q1",
                failure_reason="Hard block",
                remediation_required=False,
            )
        ],
    )


@pytest.mark.asyncio
async def test_rule_4_confidence_floor_forces_refer(store):
    app_id = "biz-1"
    await _seed_loan_after_credit(store, app_id, agent_id="agentA", session_id="s1", model_version="credit-v1")
    await _seed_compliance_passed(store, app_id)
    await _seed_agent_session(store, "agentA", "s1", model_version="m1")

    with pytest.raises(DomainError):
        await handle_generate_decision(
            {
                "application_id": app_id,
                "orchestrator_agent_id": "orch-1",
                "recommendation": "APPROVE",
                "confidence_score": 0.5,  # < 0.6
                "contributing_agent_sessions": ["agent-agentA-s1"],
                "decision_basis_summary": "basis",
                "model_versions": {"agentA": "m1"},
            },
            store,
        )


@pytest.mark.asyncio
async def test_rule_5_compliance_dependency_blocks_approval(store):
    app_id = "biz-2"
    await _seed_loan_after_credit(store, app_id, agent_id="agentA", session_id="s1", model_version="credit-v1")
    await _seed_compliance_hard_block(store, app_id)
    await _seed_agent_session(store, "agentA", "s1", model_version="m1")

    with pytest.raises(DomainError):
        await handle_generate_decision(
            {
                "application_id": app_id,
                "orchestrator_agent_id": "orch-1",
                "recommendation": "APPROVE",
                "confidence_score": 0.8,
                "contributing_agent_sessions": ["agent-agentA-s1"],
                "decision_basis_summary": "basis",
                "model_versions": {"agentA": "m1"},
            },
            store,
        )


@pytest.mark.asyncio
async def test_rule_6_causal_chain_enforces_contributing_sessions(store):
    app_id = "biz-3"
    await _seed_loan_after_credit(store, app_id, agent_id="agentA", session_id="s1", model_version="credit-v1")
    await _seed_compliance_passed(store, app_id)
    await _seed_agent_session(store, "agentA", "s1", model_version="m1")
    # Contributing session not present in credit_analysis_sessions
    await _seed_agent_session(store, "agentB", "s2", model_version="m2")

    with pytest.raises(DomainError):
        await handle_generate_decision(
            {
                "application_id": app_id,
                "orchestrator_agent_id": "orch-1",
                "recommendation": "REFER",
                "confidence_score": 0.4,
                "contributing_agent_sessions": ["agent-agentB-s2"],
                "decision_basis_summary": "basis",
                "model_versions": {"agentB": "m2"},
            },
            store,
        )


@pytest.mark.asyncio
async def test_rule_2_agent_context_loaded_required_for_contributing_sessions(store):
    app_id = "biz-4"
    await _seed_loan_after_credit(store, app_id, agent_id="agentA", session_id="s1", model_version="credit-v1")
    await _seed_compliance_passed(store, app_id)
    # Intentionally do NOT seed agent session stream with AgentContextLoaded.

    with pytest.raises(DomainError):
        await handle_generate_decision(
            {
                "application_id": app_id,
                "orchestrator_agent_id": "orch-1",
                "recommendation": "REFER",
                "confidence_score": 0.4,
                "contributing_agent_sessions": ["agent-agentA-s1"],
                "decision_basis_summary": "basis",
                "model_versions": {"agentA": "m1"},
            },
            store,
        )


@pytest.mark.asyncio
async def test_rule_3_model_version_locking(store):
    app_id = "biz-5"
    await _seed_loan_after_credit(store, app_id, agent_id="agentA", session_id="s1", model_version="credit-v1")
    await _seed_compliance_passed(store, app_id)
    await _seed_agent_session(store, "agentA", "s1", model_version="m1")

    with pytest.raises(DomainError):
        await handle_generate_decision(
            {
                "application_id": app_id,
                "orchestrator_agent_id": "orch-1",
                "recommendation": "REFER",
                "confidence_score": 0.4,
                "contributing_agent_sessions": ["agent-agentA-s1"],
                "decision_basis_summary": "basis",
                # Expected model version mismatch:
                "model_versions": {"agentA": "m2"},
            },
            store,
        )


@pytest.mark.asyncio
async def test_rule_1_state_machine_requires_credit_analysis_complete(store):
    app_id = "biz-6"
    # Loan stream has not reached ANALYSIS_COMPLETE.
    await store.append(
        stream_id=f"loan-{app_id}",
        expected_version=-1,
        events=[
            ApplicationSubmitted(
                application_id=app_id,
                applicant_id="applicant-1",
                requested_amount_usd=1000,
                loan_purpose="WorkingCapital",
                submission_channel="api",
                submitted_at=datetime.now(timezone.utc),
            )
        ],
    )
    await _seed_compliance_passed(store, app_id)
    await _seed_agent_session(store, "agentA", "s1", model_version="m1")

    with pytest.raises(DomainError):
        await handle_generate_decision(
            {
                "application_id": app_id,
                "orchestrator_agent_id": "orch-1",
                "recommendation": "REFER",
                "confidence_score": 0.4,
                "contributing_agent_sessions": ["agent-agentA-s1"],
                "decision_basis_summary": "basis",
                "model_versions": {"agentA": "m1"},
            },
            store,
        )


@pytest.mark.asyncio
async def test_compliance_dependency_before_human_approval_override(store):
    """
    If compliance has a hard block, even a human override to APPROVE must fail.
    """
    app_id = "biz-7"
    await _seed_loan_after_credit(store, app_id, agent_id="agentA", session_id="s1", model_version="credit-v1")
    await _seed_compliance_hard_block(store, app_id)
    await _seed_agent_session(store, "agentA", "s1", model_version="m1")

    # Decision should still be allowed (recommendation != APPROVE).
    await handle_generate_decision(
        {
            "application_id": app_id,
            "orchestrator_agent_id": "orch-1",
            "recommendation": "REFER",
            "confidence_score": 0.4,
            "contributing_agent_sessions": ["agent-agentA-s1"],
            "decision_basis_summary": "basis",
            "model_versions": {"agentA": "m1"},
        },
        store,
    )

    with pytest.raises(DomainError):
        await handle_human_review_completed(
            {
                "application_id": app_id,
                "reviewer_id": "LO-Sarah-Chen",
                "final_decision": "APPROVE",
                "override": True,
                "override_reason": "Override attempted despite compliance hard block",
            },
            store,
        )

