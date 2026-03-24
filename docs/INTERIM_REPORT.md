# Interim Submission Report

**TRP1 Week 5: The Ledger — Interim Deliverable**

---

## 1. Conceptual Foundations

*Full detail in `docs/DOMAIN_NOTES.md`. Summary below.*

### EDA vs ES Distinction

- **EDA:** Callback tracing is fire-and-forget; events can be dropped.
- **ES:** Ledger events are the permanent record; they cannot be lost.
- **Redesign:** Callbacks → append-only `events`; mutable updates → OCC in `event_streams`; ad-hoc reads → replay/projections.
- **Gains:** Reproducibility, temporal compliance reconstruction, deterministic conflict handling.

### Aggregate Boundary — Alternative and Failure Mode

- **Chosen:** `ComplianceRecord` separate from `LoanApplication` (`compliance-{application_id}` vs `loan-{application_id}`).
- **Rejected alternative:** Merge compliance events into `loan-{application_id}`.
- **Coupling:** A `ComplianceRuleFailed` write would require a lock on the same `loan-{application_id}` stream used by decision writes.
- **Failure mode:** Compliance agent and decision orchestrator contend for one stream row lock → one OCC-fails → under burst load, compliance activity delays decision commits (cross-concern contention).

---

## 2. Operational Mechanics

### Concurrency Control — Full Sequence

1. Both agents read `loan-X` at version 3.
2. Both call `append(..., expected_version=3)`.
3. First write succeeds via DB-level version check; `current_version` → 4.
4. Second write fails version check → `OptimisticConcurrencyError(stream_id, expected=3, actual=4)`.
5. **Losing agent:** Reload stream → inspect new event → decide if action still valid → retry with `expected_version=4` or abandon. Enforce retry budget.

*See sequence diagram in Section 4.*

### Projection Lag — System Response and UI Contract

- **System response:** API returns `projection_lag_ms` and `as_of`; optional strong-consistency fallback for critical reads.
- **UI contract:** Show "last updated" timestamp; if lag > 500ms, show "updating" indicator and optional "Refresh" (strong read).
- **Interpretation:** Sub-500ms lag is an accepted CQRS tradeoff, not a system error.

---

## 3. Advanced Patterns

### Upcasting — Concrete Function and Field-Level Reasoning

Structurally correct upcaster in `src/upcasting/upcasters.py`:

```python
@registry.register("CreditAnalysisCompleted", from_version=1)
def upcast_credit_v1_to_v2(payload: dict) -> dict:
    return {
        **payload,
        "model_version": "legacy-pre-2026",  # inferred from recorded_at
        "confidence_score": None,             # genuinely unknown — do not fabricate
        "regulatory_basis": None,             # infer only when rule-version map exists
    }
```

- **confidence_score = null:** Fabricating a never-computed score would corrupt analytics and regulatory records. Null signals absence; fabrication signals false precision.
- **model_version:** Inferred from `recorded_at` vs deployment timeline; approximate, flagged in metadata.
- **regulatory_basis:** Inferred from rule versions at `recorded_at`; if mapping missing → null.

### Distributed Projection Coordination

- **Primitive:** PostgreSQL advisory lock or `projection_leases` table (owner, heartbeat, expires_at).
- **Failure mode:** Two nodes process same batch → duplicate writes → corrupted aggregated metrics.
- **Recovery path:** Leader fails → lease expires → follower acquires → resumes from `projection_checkpoints.last_position`; idempotent handlers handle overlap.

---

## 4. Architecture Diagram (Mermaid)

*Reader can trace a single event from command input to stored event using only this diagram.*

### Command-to-Append Pipeline

```mermaid
flowchart TB
    subgraph Input
        C[Command Input]
    end

    C --> H[Command Handler]
    H --> L[Load Stream]
    L --> A[Aggregate Rebuild]
    A --> V[Validation]
    V --> D[Determine Events]

    subgraph TX["Single DB Transaction"]
        D --> S1[Lock event_streams FOR UPDATE]
        S1 --> S2[INSERT events]
        S2 --> S3[INSERT outbox]
        S3 --> S4[UPDATE current_version]
    end

    S2 --> EV[(events)]
    S3 --> OB[(outbox)]

    EV --> A1
    EV --> A2
    EV --> A3

    subgraph Aggregates["Aggregate Boundaries (stream_id formats)"]
        A1["LoanApplication<br/>stream_id: loan-{application_id}"]
        A2["AgentSession<br/>stream_id: agent-{agent_id}-{session_id}"]
        A3["ComplianceRecord<br/>stream_id: compliance-{application_id}"]
    end
```

**Diagram check:**
- Event store central (events + event_streams).
- At least three aggregates with stream ID formats.
- Command path directional and labeled.
- Outbox in same transaction.

### Concurrency Sequence (Including Losing Agent Steps)

```mermaid
sequenceDiagram
    participant A as Agent A
    participant B as Agent B
    participant ES as EventStore
    participant DB as PostgreSQL

    A->>ES: append(loan-X, expected_version=3)
    B->>ES: append(loan-X, expected_version=3)

    ES->>DB: Tx-A: SELECT FOR UPDATE
    DB-->>ES: current_version=3
    ES->>DB: INSERT events, outbox; UPDATE version=4
    DB-->>ES: commit
    ES-->>A: success(4)

    ES->>DB: Tx-B: SELECT FOR UPDATE
    DB-->>ES: current_version=4
    ES-->>B: OptimisticConcurrencyError(expected=3, actual=4)

    Note over B: Losing agent: reload stream,<br/>inspect new event, retry or abandon
```

---

## 5. Progress Summary

| Category | Components |
|----------|------------|
| **Working** | Schema (events, event_streams, projection_checkpoints, outbox), EventStore (all 6 methods, OCC, outbox in same tx), domain models, aggregates (LoanApplication, AgentSession), command handlers (submit, credit_analysis, start_session), concurrency test |
| **In progress** | Full lifecycle state machine, projection daemon transactional checkpoint |
| **Not started** | Distributed projection lease protocol, MCP transport lifecycle test |

---

## 6. Concurrency Test Evidence

**Run (use `-s` to show assertion evidence in output):**

First-time setup:
```powershell
.\scripts\run_setup.ps1
```
(Or run `scripts\setup_db.sql` as postgres superuser manually.)

Then:
```powershell
$env:DATABASE_URL="postgresql://bnobody:beahhal@localhost:5432/z_ledger"
python -m pytest tests/test_concurrency.py -v -s
```

**Required assertions (all must pass; evidence printed explicitly):**
1. Total stream length = 4 after both tasks complete.
2. Winning task reports `stream_position=4`.
3. Losing task raises `OptimisticConcurrencyError` (explicitly asserted, not swallowed).

**The test prints this block so it appears in the report:**
```
--- CONCURRENCY TEST EVIDENCE ---
Assertion 1 - Total stream length: 4 (expected 4)
Assertion 2 - Winning task stream_position: 4 (expected 4)
Assertion 3 - Losing task raised: OptimisticConcurrencyError(stream_id='...', expected_version=3, actual_version=4)
---------------------------------
```

### Test Output (actual run)

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\Users\Bnobody_47\Documents\Z Ledger
configfile: pyproject.toml
collected 1 item

tests/test_concurrency.py::test_double_decision_concurrency
--- CONCURRENCY TEST EVIDENCE ---
Assertion 1 - Total stream length: 4 (expected 4)
Assertion 2 - Winning task stream_position: 4 (expected 4)
Assertion 3 - Losing task raised: OptimisticConcurrencyError(stream_id='loan-app-concurrency-1', expected_version=3, actual_version=4)
---------------------------------

PASSED

============================== 1 passed in 0.40s ===============================
```

**Evidence checklist (all met):**
- **Total stream length = 4** — Assertion 1 explicitly confirms.
- **Winning task stream_position = 4** — Assertion 2 explicitly confirms.
- **Losing task raises OptimisticConcurrencyError** — Assertion 3 shows the full exception with `stream_id`, `expected_version=3`, `actual_version=4`.

**Connection help:** If you get `InvalidPasswordError`, use your real Postgres credentials in `DATABASE_URL` (user/password). Create the DB with `createdb z_ledger` if it does not exist.

---

## 7. Gap Analysis

| Gap | Component | Reason | Fix |
|-----|-----------|--------|-----|
| A | Projection daemon | Checkpoint update not in same transaction as projection write | Wrap both in single tx; crash between them causes reprocessing |
| B | Aggregate state machine | Exhaustive invalid-transition tests not complete | Add negative tests per state/event pair |
| C | MCP lifecycle | Handler logic validated; transport contract not | Add integration test driving flow via MCP tools only |
| D | Distributed daemon | Single-node only; multi-node lease not implemented | Add `projection_leases` + heartbeat; document recovery path |

---

## 8. Final Submission Plan (Sequenced)

1. Lock write-side: finish aggregate transition tests, freeze schema.
2. Harden read-side: transactional checkpoint coupling, lag SLO test.
3. Phase 4: upcasting immutability proof, integrity chain.
4. Phase 5: MCP lifecycle test via tools/resources only.
5. Capture test evidence, update report with real output.

---

## 9. Verification Commands

```powershell
python -m pip install -e ".[dev]"
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/z_ledger"
python -m pytest tests/test_concurrency.py -v
python -m pytest -q
```
