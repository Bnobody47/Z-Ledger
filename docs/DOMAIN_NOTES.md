## DOMAIN_NOTES (graded deliverable)

Fill this in **before** we implement the Ledger. This file is assessed independently of code.

### 1) EDA vs ES distinction
- **Today’s system (callbacks/traces)**
  - Notes:
- **Redesign using The Ledger**
  - What changes:
  - What we gain:

### 2) Aggregate boundaries (and one rejected alternative)
- **Chosen aggregates**
  - `LoanApplication`:
  - `AgentSession`:
  - `ComplianceRecord`:
  - `AuditLedger`:
- **Rejected alternative boundary**
  - Alternative:
  - Why rejected / coupling failure mode prevented:

### 3) Concurrency in practice (expected_version collision)
- Sequence of operations:
- What the losing agent receives:
- What it must do next:

### 4) Projection lag and consequences (UI contract)
- What the system does when read-model lags:
- How the UI communicates it:

### 5) Upcasting scenario (CreditDecisionMade schema evolution)
- Upcaster v1 → v2:
- Inference strategy for `model_version`:
- When we choose `null` vs inference:

### 6) Marten Async Daemon parallel (distributed projections)
- How we’d distribute projection execution in Python:
- Coordination primitive:
- Failure mode it guards against:

