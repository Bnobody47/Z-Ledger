"""
Command handlers following load → validate → determine → append pattern.
At minimum: handle_credit_analysis_completed, handle_submit_application.
Full set: submit_application, credit_analysis_completed, fraud_screening_completed,
compliance_check, generate_decision, human_review_completed, start_agent_session.
"""
from src.event_store import EventStore
from src.aggregates.loan_application import LoanApplicationAggregate
from src.aggregates.agent_session import AgentSessionAggregate


async def handle_submit_application(cmd: dict, store: EventStore) -> None:
    """Submit a new loan application."""
    raise NotImplementedError


async def handle_credit_analysis_completed(cmd: dict, store: EventStore) -> None:
    """Record CreditAnalysisCompleted. Requires active AgentSession with context loaded."""
    raise NotImplementedError


async def handle_fraud_screening_completed(cmd: dict, store: EventStore) -> None:
    """Record FraudScreeningCompleted."""
    raise NotImplementedError


async def handle_compliance_check(cmd: dict, store: EventStore) -> None:
    """Record ComplianceRulePassed or ComplianceRuleFailed."""
    raise NotImplementedError


async def handle_generate_decision(cmd: dict, store: EventStore) -> None:
    """Generate DecisionGenerated. All required analyses must be present."""
    raise NotImplementedError


async def handle_human_review_completed(cmd: dict, store: EventStore) -> None:
    """Record HumanReviewCompleted."""
    raise NotImplementedError


async def handle_start_agent_session(cmd: dict, store: EventStore) -> None:
    """Start agent session (AgentContextLoaded). Gas Town: required before any agent decision."""
    raise NotImplementedError
