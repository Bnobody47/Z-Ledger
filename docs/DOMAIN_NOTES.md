## DOMAIN_NOTES (graded deliverable)

### 1) EDA vs ES distinction
- Callback traces are **EDA**: event-like notifications that can be dropped and are not authoritative state.
- The Ledger is **ES**: every state change is an immutable stored fact in `events`.
- Redesign impact:
  - Command handlers append domain events instead of writing mutable rows.
  - Read models are projections rebuilt from events.
  - We gain replayability, temporal debugging, and a regulator-verifiable audit trail.

### 2) Aggregate boundaries (and one rejected alternative)
- Chosen boundaries:
  - `LoanApplication` (`loan-{id}`): application lifecycle invariants.
  - `AgentSession` (`agent-{agent_id}-{session_id}`): session context + model/version trace.
  - `ComplianceRecord` (`compliance-{application_id}`): compliance checks and rule history.
  - `AuditLedger` (`audit-{entity_type}-{entity_id}`): integrity checks and cross-stream audit chain.
- Rejected alternative:
  - Merge `ComplianceRecord` into `LoanApplication`.
  - Rejected because compliance and decision writes would contend on one stream, increasing OCC conflicts and coupling compliance rule changes to core loan lifecycle logic.

### 3) Concurrency in practice (expected_version collision)
- Sequence:
  1. Agent A and Agent B both load `loan-X` at version 3.
  2. Both call `append(... expected_version=3)`.
  3. One transaction acquires stream row lock first and appends position 4.
  4. Second transaction sees `current_version=4` and fails.
- Losing agent receives `OptimisticConcurrencyError` with expected and actual versions.
- Next action: reload stream, recompute command against latest facts, retry within retry budget.

### 4) Projection lag and consequences (UI contract)
- System behavior:
  - Write-side stream reads are immediately consistent.
  - Projection reads are eventually consistent and expose lag metric.
- UI contract:
  - For safety-critical reads, UI can request direct stream-backed confirmation or show “updating…” badge when lag exceeds threshold.
  - Responses can include `as_of` or projection lag metadata.

### 5) Upcasting scenario (CreditDecisionMade schema evolution)
- Upcaster strategy v1→v2:
  - Add missing fields at read time only.
  - Stored event remains unchanged in DB.
- Inference strategy:
  - `model_version`: infer fallback marker for historical unknowns (e.g., `legacy-pre-2026`).
  - `confidence_score`: `null` when unknown.
  - `regulatory_basis`: infer only where source-of-truth exists; otherwise null.
- Rule: choose null over fabrication when inferred value could affect decisions/compliance interpretation.

### 6) Marten Async Daemon parallel (distributed projections)
- Python analogue:
  - Multiple daemon workers partition projection ownership or stream ranges.
  - Each projection keeps independent checkpoint in `projection_checkpoints`.
- Coordination primitive:
  - Postgres row-level locking/checkpoint ownership via transactional updates.
- Failure mode prevented:
  - Duplicate or out-of-order projection processing after crash/restart (idempotent handlers + checkpoints limit damage and allow safe resume).

