## DESIGN (graded deliverable)

### 1) Aggregate boundary justification
- `ComplianceRecord` is separate from `LoanApplication` to isolate rule churn from lifecycle churn.
- If merged, compliance rule fan-out and loan decision fan-out contend on one stream and increase OCC collisions.
- Failure mode if merged: concurrent compliance updates can block loan finalization path and force unrelated retries.

### 2) Projection strategy + SLOs
- **ApplicationSummary**
  - Strategy: async projection via daemon.
  - SLO: p99 < 50ms query latency, lag target < 500ms normal load.
- **AgentPerformanceLedger**
  - Strategy: async aggregate metrics updates.
  - SLO: p99 < 50ms, lag tolerance up to 2s.
- **ComplianceAuditView**
  - Strategy: append snapshots per compliance event (`projection_compliance_audit`) with `as_of`.
  - Invalidation: rebuild from stream on schema handler changes.
  - SLO: p99 < 200ms, lag <= 2s.

### 3) Concurrency analysis + retry budget
- Under 100 concurrent applications and 4 agents/app, expected hot-stream OCC collision rate is low-to-moderate (mostly when same app is processed in parallel).
- Retry strategy:
  - Immediate reload, re-validate invariants, exponential backoff (50ms, 100ms, 200ms).
- Retry budget:
  - Max 3 retries, then return typed failure.

### 4) Upcasting inference decisions
- `CreditAnalysisCompleted`:
  - `model_version`: inferred fallback label (`legacy-pre-2026`) where unknown.
  - `confidence_score`: null if missing historically.
  - `regulatory_basis`: nullable inference from regulation version metadata.
- Consequence model:
  - Incorrect inference risks compliance misinterpretation.
  - Null preserves epistemic honesty and avoids false certainty.

### 5) EventStoreDB comparison (concept mapping)
- Stream IDs map directly (`loan-{id}`, `agent-{id}-{session}`).
- `load_all()` maps to EventStoreDB `$all` stream reads.
- ProjectionDaemon maps to persistent subscriptions/checkpointing.
- EventStoreDB provides built-in subscription mechanics and operational tooling; PostgreSQL implementation requires custom daemon, poison-event handling, and lag instrumentation.

### 6) What we’d do differently with one more day
- Reconsider projection daemon partitioning and poison queue design.
- Current single-loop model is good baseline but should be upgraded to distributed ownership with per-projection dead-letter stream and explicit replay tooling.

