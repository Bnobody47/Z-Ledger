## DESIGN (graded deliverable)

This doc is assessed with equal weight to code. It must explain **tradeoffs** and **quantitative commitments**.

### 1) Aggregate boundary justification
- Why `ComplianceRecord` is separate from `LoanApplication`:
- What would couple if merged:
- Concrete concurrent-write failure mode:

### 2) Projection strategy + SLOs
- **ApplicationSummary**
  - Inline vs async:
  - SLO:
- **AgentPerformanceLedger**
  - Inline vs async:
  - SLO:
- **ComplianceAuditView**
  - Temporal query snapshot strategy:
  - Snapshot invalidation logic:
  - SLO:

### 3) Concurrency analysis + retry budget
- Expected OptimisticConcurrencyError rate under peak:
- Retry strategy:
- Max retry budget before failing:

### 4) Upcasting inference decisions
- For each inferred field:
  - Likely error rate:
  - Downstream consequence:
  - Null vs inference rationale:

### 5) EventStoreDB comparison (concept mapping)
- Streams:
- `$all` vs `load_all()`:
- Persistent subscriptions vs ProjectionDaemon:
- What EventStoreDB provides that we must build:

### 6) What we’d do differently with one more day
- Single most significant decision to reconsider:
- Why:

