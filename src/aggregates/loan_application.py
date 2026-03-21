"""
LoanApplicationAggregate: state machine, event replay via load(), _apply handlers.
Stream: loan-{application_id}
"""
from enum import Enum
from src.models.events import StoredEvent
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

    def _on_ApplicationApproved(self, event: StoredEvent) -> None:
        self.state = ApplicationState.FINAL_APPROVED
        self.approved_amount = event.payload.get("approved_amount_usd")

    def _on_CreditAnalysisCompleted(self, event: StoredEvent) -> None:
        self.state = ApplicationState.ANALYSIS_COMPLETE
