"""
LoanApplicationAggregate: state machine, event replay via load(), _apply handlers.
Stream: loan-{application_id}
"""
from enum import Enum
from src.models.events import DomainError, StoredEvent
from src.event_store import EventStore


class ApplicationState(str, Enum):
    SUBMITTED = "SUBMITTED"
    AWAITING_ANALYSIS = "AWAITING_ANALYSIS"
    ANALYSIS_COMPLETE = "ANALYSIS_COMPLETE"
    COMPLIANCE_REVIEW = "COMPLIANCE_REVIEW"
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

    def _on_ApplicationApproved(self, event: StoredEvent) -> None:
        self.state = ApplicationState.FINAL_APPROVED
        self.approved_amount = event.payload.get("approved_amount_usd")

    def _on_CreditAnalysisCompleted(self, event: StoredEvent) -> None:
        self.state = ApplicationState.ANALYSIS_COMPLETE

    def _on_ComplianceCheckRequested(self, event: StoredEvent) -> None:
        self.state = ApplicationState.COMPLIANCE_REVIEW

    def _on_DecisionGenerated(self, event: StoredEvent) -> None:
        recommendation = event.payload.get("recommendation")
        if recommendation == "APPROVE":
            self.state = ApplicationState.APPROVED_PENDING_HUMAN
        elif recommendation == "DECLINE":
            self.state = ApplicationState.DECLINED_PENDING_HUMAN
        else:
            self.state = ApplicationState.PENDING_DECISION

    def _on_ApplicationDeclined(self, event: StoredEvent) -> None:
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
