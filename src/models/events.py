"""Core event models and domain exceptions."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseEvent(BaseModel):
    """Base event object used by EventStore append operations."""

    model_config = ConfigDict(extra="forbid")
    event_type: str
    event_version: int = 1

    def payload(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        data.pop("event_type", None)
        data.pop("event_version", None)
        return data


class ApplicationSubmitted(BaseEvent):
    event_type: Literal["ApplicationSubmitted"] = "ApplicationSubmitted"
    application_id: str
    applicant_id: str
    requested_amount_usd: float
    loan_purpose: str
    submission_channel: str
    submitted_at: datetime


class CreditAnalysisRequested(BaseEvent):
    event_type: Literal["CreditAnalysisRequested"] = "CreditAnalysisRequested"
    application_id: str
    assigned_agent_id: str
    requested_at: datetime
    priority: str = "NORMAL"


class CreditAnalysisCompleted(BaseEvent):
    event_type: Literal["CreditAnalysisCompleted"] = "CreditAnalysisCompleted"
    application_id: str
    agent_id: str
    session_id: str
    model_version: str
    confidence_score: float
    risk_tier: str
    recommended_limit_usd: float
    analysis_duration_ms: int
    input_data_hash: str


class AgentContextLoaded(BaseEvent):
    event_type: Literal["AgentContextLoaded"] = "AgentContextLoaded"
    agent_id: str
    session_id: str
    context_source: str
    event_replay_from_position: int
    context_token_count: int
    model_version: str


class ComplianceRulePassed(BaseEvent):
    event_type: Literal["ComplianceRulePassed"] = "ComplianceRulePassed"
    application_id: str
    rule_id: str
    rule_version: str
    evaluation_timestamp: datetime
    evidence_hash: str


class ComplianceRuleFailed(BaseEvent):
    event_type: Literal["ComplianceRuleFailed"] = "ComplianceRuleFailed"
    application_id: str
    rule_id: str
    rule_version: str
    failure_reason: str
    remediation_required: bool = False


class DecisionGenerated(BaseEvent):
    event_type: Literal["DecisionGenerated"] = "DecisionGenerated"
    application_id: str
    orchestrator_agent_id: str
    recommendation: str
    confidence_score: float
    contributing_agent_sessions: list[str]
    decision_basis_summary: str
    model_versions: dict[str, str] | None = None


class FraudScreeningCompleted(BaseEvent):
    event_type: Literal["FraudScreeningCompleted"] = "FraudScreeningCompleted"
    application_id: str
    agent_id: str
    fraud_score: float
    anomaly_flags: list[str]
    screening_model_version: str
    input_data_hash: str


class HumanReviewCompleted(BaseEvent):
    event_type: Literal["HumanReviewCompleted"] = "HumanReviewCompleted"
    application_id: str
    reviewer_id: str
    override: bool
    final_decision: str
    override_reason: str | None = None


class StoredEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    stream_id: str
    stream_position: int
    global_position: int
    event_type: str
    event_version: int
    payload: dict[str, Any]
    metadata: dict[str, Any]
    recorded_at: datetime

    def with_payload(self, payload: dict[str, Any], version: int) -> "StoredEvent":
        return self.model_copy(update={"payload": payload, "event_version": version})


class StreamMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stream_id: str
    aggregate_type: str
    current_version: int
    created_at: datetime
    archived_at: datetime | None
    metadata: dict[str, Any]


class OptimisticConcurrencyError(Exception):
    stream_id: str
    expected_version: int
    actual_version: int

    def __init__(self, message: str, stream_id: str, expected_version: int, actual_version: int):
        super().__init__(message)
        self.stream_id = stream_id
        self.expected_version = expected_version
        self.actual_version = actual_version


class DomainError(Exception):
    pass
