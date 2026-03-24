# DOMAIN_NOTES (Graded Deliverable)

## 1) EDA vs ES Distinction

**EDA (Event-Driven Architecture):** Callback-based tracing is EDA because events act as fire-and-forget notifications. They can be dropped, duplicated, or lost by consumers without affecting the source system's storage model — the "truth" lives elsewhere (e.g., a mutable database row).

**ES (Event Sourcing):** The Ledger uses Event Sourcing because events in the `events` table are the permanent record. If an event is lost, history and state reconstruction are broken. Events cannot be dropped; they are the source of truth.

**Concrete redesign — components that change:**

| Before (EDA/callback) | After (ES/Ledger) |
|----------------------|-------------------|
| Callbacks write to log/trace storage | Command handlers append to `events` via `EventStore.append()` |
| Mutable status columns updated in place | Append-only stream; state derived by replay |
| Ad-hoc reads from latest row | Replay from `events` or read from projections |

**Explicit gains:**
- **Reproducibility:** Decision history is replayable end-to-end.
- **Temporal auditability:** Compliance can reconstruct state at any past timestamp.
- **Deterministic conflict handling:** OCC gives clear retry/abandon semantics under concurrent writers.

---

## 2) Aggregate Boundaries — Alternative and Failure Mode

**Chosen boundaries (4 aggregates):**

| Aggregate | Stream ID Format | Purpose |
|-----------|------------------|---------|
| LoanApplication | `loan-{application_id}` | Application lifecycle |
| AgentSession | `agent-{agent_id}-{session_id}` | Agent context and model version |
| ComplianceRecord | `compliance-{application_id}` | Regulatory checks |
| AuditLedger | `audit-{entity_type}-{entity_id}` | Integrity chain |

**Rejected alternative:** Merge `ComplianceRecord` into `LoanApplication` — i.e., append `ComplianceRulePassed` and `ComplianceRuleFailed` to the `loan-{application_id}` stream.

**Coupling introduced by merge:**
- A `ComplianceRuleFailed` write would require a lock on the same `loan-{application_id}` stream row used by decision writes (e.g., `DecisionGenerated`, `ApplicationApproved`).

**Specific failure mode under concurrent writes:**
- Compliance agent and decision orchestrator both append to `loan-{application_id}`.
- Both contend for `SELECT ... FOR UPDATE` on the same `event_streams` row.
- One succeeds; the other receives `OptimisticConcurrencyError` and must retry.
- Under burst load, compliance activity directly causes write contention and retries on the decision path, delaying final approval/decline.
- Cross-concern lock contention: unrelated compliance updates block or delay decision commits.

**Why separation helps:** `ComplianceRecord` uses `compliance-{application_id}`; decision uses `loan-{application_id}`. Different stream rows → no shared lock → no cross-concern contention.

---

## 3) Concurrency Control — Full Sequence

1. Agent A reads `loan-X`, sees `current_version = 3`.
2. Agent B reads `loan-X`, sees `current_version = 3`.
3. Both call `append(stream_id="loan-X", events=[...], expected_version=3)`.
4. Transaction A acquires `event_streams` row lock first (`SELECT ... FOR UPDATE`).
5. Transaction A inserts event at `stream_position=4`, inserts outbox row, updates `current_version=4`, commits.
6. Transaction B acquires the row lock, reads `current_version=4`, compares to expected 3, and raises `OptimisticConcurrencyError(stream_id="loan-X", expected_version=3, actual_version=4)`.
7. **Losing agent's next steps:**
   - Catch `OptimisticConcurrencyError`.
   - Reload the stream (`load_stream("loan-X")`).
   - Inspect the newly appended event — was another agent's work sufficient? Is our action still valid?
   - If still valid: retry append with `expected_version=4`.
   - If superseded: abandon and return typed conflict to caller.
   - Enforce retry budget (e.g., max 3 retries) before failing.

---

## 4) Projection Lag — System Response and UI Contract

**Problem:** A projection serves a stale read when the daemon has not yet processed the latest events.

**System response (what the system does):**
- API returns projection data plus metadata: `projection_lag_ms`, `as_of` (timestamp of last processed event).
- For critical reads (e.g., "available credit limit" after disbursement): optional strong-consistency fallback — read directly from the aggregate stream instead of the projection.
- Health endpoint exposes `get_lag()` per projection so UIs and operators can detect lag.

**UI contract:**
- Display a "last updated" timestamp alongside projection-backed data.
- If `projection_lag_ms` > threshold (e.g., 500ms): show an "updating" indicator and optionally a "Refresh" action that triggers strong-consistency read.
- Never present projection data as guaranteed real-time unless lag is within SLO.

**Interpretation:** Sub-500ms lag is an accepted CQRS tradeoff for lower write latency and scalable read models — it is not a system error when within SLO.

---

## 5) Upcasting — Structurally Correct Function and Field-Level Reasoning

**Structurally correct upcaster (CreditAnalysisCompleted v1→v2):**

```python
@registry.register("CreditAnalysisCompleted", from_version=1)
def upcast_credit_v1_to_v2(payload: dict) -> dict:
    return {
        **payload,
        "model_version": _infer_model_version(payload.get("recorded_at")),
        "confidence_score": None,
        "regulatory_basis": _infer_regulatory_basis(payload.get("recorded_at")),
    }

def _infer_model_version(recorded_at) -> str:
    # Inferred from recorded_at against known deployment timeline.
    # Flag as approximate in metadata — we don't know exactly which build.
    return "legacy-pre-2026" if recorded_at else "unknown"

def _infer_regulatory_basis(recorded_at) -> list | None:
    # Inferred from rule versions active at recorded_at date.
    # If mapping missing, return null — do not fabricate.
    return None  # or lookup from regulation_versions_by_date
```

**Field-level inference strategy:**

| Field | Strategy | Rationale |
|-------|----------|-----------|
| `confidence_score` | **null** when absent in v1 | A score that was never computed must not be invented. Fabrication would corrupt analytics and regulatory records with false precision. Null signals genuine absence. |
| `model_version` | Inferred from `recorded_at` vs deployment timeline | Approximate only; we know era, not exact build. Acceptable with metadata annotation. |
| `regulatory_basis` | Inferred from rule versions active at `recorded_at` | If mapping exists, use it. If not, return null — never fabricate regulation IDs. |

**Rule:** Genuinely unknown → null. Inferrable with documented uncertainty → inference with annotation is acceptable.

---

## 6) Distributed Projection Coordination — Primitive and Recovery Path

**Coordination primitive:** PostgreSQL advisory lock or a dedicated `projection_leases` table (projection_name, owner_id, heartbeat_at, expires_at). Leader acquires lock/lease before processing; heartbeat extends lease.

**Specific failure mode guarded against:** Two daemon nodes process the same `global_position` batch concurrently → duplicate writes to projection tables → corrupted aggregated metrics (e.g., double-counted analyses, wrong averages).

**Recovery path when leader fails:**
1. Leader stops heartbeating → lease expires (or lock is released).
2. Follower detects expiry and attempts to acquire lease.
3. Follower acquires lease.
4. Follower reads `projection_checkpoints.last_position` for that projection.
5. Follower resumes processing from `last_position + 1`.
6. If leader crashed after projection write but before checkpoint update: follower may reprocess same events. Projection handlers must be idempotent (e.g., upsert by event_id or composite key) to avoid corruption.

---
