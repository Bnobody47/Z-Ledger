"""
LoanApplicationAggregate: state machine, event replay via load(), _apply handlers.
Stream: loan-{application_id}
"""
from enum import Enum
from src.models.events import (
    ComplianceRuleFailed,
    ComplianceRulePassed,
    DomainError,
    DecisionGenerated,
    HumanReviewCompleted,
    StoredEvent,
)
from src.event_store import EventStore


class ApplicationState(str, Enum):
    SUBMITTED = "SUBMITTED"
    AWAITING_ANALYSIS = "AWAITING_ANALYSIS"
    ANALYSIS_COMPLETE = "ANALYSIS_COMPLETE"
    PENDING_DECISION = "PENDING_DECISION"
    APPROVED_PENDING_HUMAN = "APPROVED_PENDING_HUMAN"
    DECLINED_PENDING_HUMAN = "DECLINED_PENDING_HUMAN"
    FINAL_APPROVED = "FINAL_APPROVED"
    FINAL_DECLINED = "FINAL_DECLINED"


class LoanApplicationAggregate:
    def __init__(self, application_id: str):
        self.application_id = application_id
        self.version = 0
        self.state: ApplicationState | None = None
        self.applicant_id: str | None = None
        self.requested_amount: float | None = None
        self.approved_amount: float | None = None
        # Causal chain inputs for DecisionGenerated: sessions that produced
        # CreditAnalysisCompleted for this loan stream.
        self.credit_analysis_sessions: set[str] = set()

    @classmethod
    async def load(cls, store: EventStore, application_id: str) -> "LoanApplicationAggregate":
        events = await store.load_stream(f"loan-{application_id}")
        agg = cls(application_id=application_id)
        for event in events:
            agg._apply(event)
        return agg

    def _apply(self, event: StoredEvent) -> None:
        handler = getattr(self, f"_on_{event.event_type}", None)
        if handler:
            handler(event)
        self.version = event.stream_position

    def _on_ApplicationSubmitted(self, event: StoredEvent) -> None:
        self.state = ApplicationState.SUBMITTED
        self.applicant_id = event.payload.get("applicant_id")
        self.requested_amount = event.payload.get("requested_amount_usd")

    def _on_CreditAnalysisRequested(self, event: StoredEvent) -> None:
        self.state = ApplicationState.AWAITING_ANALYSIS

    def _on_CreditAnalysisCompleted(self, event: StoredEvent) -> None:
        self.state = ApplicationState.ANALYSIS_COMPLETE
        agent_id = event.payload.get("agent_id")
        session_id = event.payload.get("session_id")
        if agent_id and session_id:
            self.credit_analysis_sessions.add(f"agent-{agent_id}-{session_id}")

    def _on_DecisionGenerated(self, event: StoredEvent) -> None:
        recommendation = event.payload.get("recommendation")
        if recommendation == "APPROVE":
            self.state = ApplicationState.APPROVED_PENDING_HUMAN
        elif recommendation == "DECLINE":
            self.state = ApplicationState.DECLINED_PENDING_HUMAN
        else:
            self.state = ApplicationState.PENDING_DECISION

    def _on_HumanReviewCompleted(self, event: StoredEvent) -> None:
        final_decision = event.payload.get("final_decision")
        if final_decision == "APPROVE":
            self.state = ApplicationState.FINAL_APPROVED
        else:
            self.state = ApplicationState.FINAL_DECLINED

    def assert_can_submit(self) -> None:
        if self.version != 0:
            raise DomainError("Application already submitted.")

    def assert_awaiting_credit_analysis(self) -> None:
        allowed = {ApplicationState.SUBMITTED, ApplicationState.AWAITING_ANALYSIS}
        if self.state not in allowed:
            raise DomainError(
                f"Invalid transition: credit analysis cannot be recorded from state={self.state}"
            )

    def assert_not_terminal(self) -> None:
        if self.state in {ApplicationState.FINAL_APPROVED, ApplicationState.FINAL_DECLINED}:
            raise DomainError(f"Application is terminal ({self.state}); no further transitions allowed.")

    async def _compliance_allows_approval(self, store: EventStore) -> bool:
        """
        Compliance dependency rule.
        For approval paths we require:
          - at least one ComplianceRulePassed
          - and no hard-block ComplianceRuleFailed (remediation_required=False)
        """
        compliance_events = await store.load_stream(f"compliance-{self.application_id}")
        has_passed = any(e.event_type == "ComplianceRulePassed" for e in compliance_events)
        hard_block_failed = any(
            e.event_type == "ComplianceRuleFailed" and not bool(e.payload.get("remediation_required", False))
            for e in compliance_events
        )
        return has_passed and not hard_block_failed

    @staticmethod
    def _parse_contributing_session(entry: str) -> tuple[str, str]:
        """
        Expected format: agent-{agent_id}-{session_id}
        Split on the last '-' so agent_id may contain '-' safely.
        """
        if not entry.startswith("agent-"):
            raise DomainError(f"Invalid contributing session entry: {entry!r}")
        body = entry[len("agent-") :]
        idx = body.rfind("-")
        if idx <= 0 or idx == len(body) - 1:
            raise DomainError(f"Invalid contributing session entry: {entry!r}")
        agent_id = body[:idx]
        session_id = body[idx + 1 :]
        return agent_id, session_id

    async def assert_can_generate_decision(
        self,
        store: EventStore,
        *,
        recommendation: str,
        confidence_score: float,
        contributing_agent_sessions: list[str],
        model_versions: dict[str, str] | None,
    ) -> None:
        # 1) State machine transitions.
        if self.state != ApplicationState.ANALYSIS_COMPLETE:
            raise DomainError(f"Invalid transition: generate_decision not allowed from state={self.state}")

        # 4) Confidence floor: below 0.6 forces REFER.
        if confidence_score < 0.6 and recommendation != "REFER":
            raise DomainError(
                f"Confidence floor enforced: confidence_score={confidence_score} requires recommendation='REFER'"
            )

        # 5) Compliance dependency.
        if recommendation == "APPROVE":
            if not await self._compliance_allows_approval(store):
                raise DomainError("Cannot APPROVE without compliance pass and no hard block")

        # 6) Causal chain + 2/3 context/model locking.
        if not contributing_agent_sessions:
            raise DomainError("contributing_agent_sessions must be provided for causal chain enforcement")

        if model_versions is None:
            raise DomainError("model_versions must be provided for model version locking enforcement")

        for entry in contributing_agent_sessions:
            agent_id, session_id = self._parse_contributing_session(entry)

            # Causal chain enforcement: the loan must contain a credit analysis completion
            # produced by the contributing session.
            if entry not in self.credit_analysis_sessions:
                raise DomainError(f"contributing session {entry!r} has no CreditAnalysisCompleted on this loan")

            # Context-loaded enforcement + model locking (AgentSession stream).
            agent_session_stream = f"agent-{agent_id}-{session_id}"
            agent_session_events = await store.load_stream(agent_session_stream)
            context_event = next(
                (e for e in agent_session_events if e.event_type == "AgentContextLoaded"), None
            )
            if context_event is None:
                raise DomainError(f"AgentSession {agent_session_stream} missing AgentContextLoaded")

            expected_model_version = model_versions.get(agent_id)
            actual_model_version = context_event.payload.get("model_version")
            if expected_model_version is None:
                raise DomainError(f"model_versions missing expected entry for agent_id={agent_id!r}")
            if expected_model_version != actual_model_version:
                raise DomainError(
                    f"Model version locking failed for agent_id={agent_id!r}: expected={expected_model_version!r}, actual={actual_model_version!r}"
                )

    async def assert_can_human_review(
        self,
        store: EventStore,
        *,
        final_decision: str,
        override: bool,
    ) -> None:
        # State machine transition.
        allowed_states = {ApplicationState.APPROVED_PENDING_HUMAN, ApplicationState.DECLINED_PENDING_HUMAN, ApplicationState.PENDING_DECISION}
        if self.state not in allowed_states:
            raise DomainError(f"Invalid transition: human_review not allowed from state={self.state}")

        # Rule 5 (compliance dependency) for approval outcomes.
        if final_decision == "APPROVE":
            if not await self._compliance_allows_approval(store):
                raise DomainError("Cannot APPROVE in human review without compliance pass and no hard block")

        # Override semantics: allow switching from the AI recommendation.
        if self.state == ApplicationState.APPROVED_PENDING_HUMAN and final_decision != "APPROVE" and not override:
            raise DomainError("Declining an APPROVED_PENDING_HUMAN outcome requires override=true")
        if self.state == ApplicationState.DECLINED_PENDING_HUMAN and final_decision != "DECLINE" and not override:
            raise DomainError("Approving a DECLINED_PENDING_HUMAN outcome requires override=true")
