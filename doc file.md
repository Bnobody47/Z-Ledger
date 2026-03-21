TRP1 WEEK 5: The Ledger
Agentic Event Store & Enterprise Audit Infrastructure. 
Building the immutable memory and governance backbone for multi-agent AI systems at production scale.
If 2025 was the year of the agent, 2026 is the year multi-agent systems move into production. The shift depends on one thing: infrastructure that can be trusted. An event store is not optional infrastructure for production AI. It is the foundation.
Builds on:
Week 1 Governance Hooks & Intent Traceability   
Week 2 Automaton Auditor   
Week 4 Brownfield Cartographer

Why This Project
Every system you have built in this program has a memory problem. The Cartographer's lineage graph is rebuilt from scratch on each run. The Automaton Auditor's judgements are lost when the process ends. Week 1's governance hooks produce an intent log that no other system reads. These are not bugs — they are the natural limitations of systems that have no shared, persistent, append-only memory.
The Ledger fixes this permanently. It is the event store that all other systems in this program should have been writing to from Week 1. By the end of this week, you will have a production-quality event sourcing infrastructure that: makes agent decisions auditable and reproducible, enables temporal queries for compliance and debugging, provides the append-only ledger that prevents the ephemeral memory failure mode described in the Gas Town pattern, and exposes everything as a typed, queryable API that downstream systems can consume.
The business case is precise. In 2026, the number-one reason enterprise AI deployments fail to reach production is not model quality — it is governance and auditability. Regulators, auditors, and enterprise risk teams require an immutable record of every AI decision and the data that informed it. The Ledger is that record. An FDE who can deploy it in the first week of a client engagement immediately unblocks the governance conversation that is otherwise the last thing to get resolved.

The Compounding Connection
This project is the retroactive foundation for the entire program. When you build the Ledger, you are building the infrastructure that all prior projects should have been using. Your Week 2 audit verdicts become events in a GovernanceJudgement stream. The Ledger does not add a new system — it connects the ones you already have.

New Skills This Week
Technical Skills
Event store schema design: Append-only tables, stream partitioning, hot/cold storage, PostgreSQL LISTEN/NOTIFY for real-time subscriptions
CQRS implementation: Separating command handlers from query handlers, projection management, eventual consistency patterns
Aggregate design: Consistency boundaries, business rule enforcement in domain logic, state machine patterns
Optimistic concurrency control: Version-based conflict detection, retry strategies, conflict resolution patterns
Async projection daemon: Checkpoint management, fault-tolerant background processing, projection lag measurement
Upcasting & schema evolution: Version migration chains, inference vs. null strategies, immutability guarantees
Cryptographic audit chains: Hash chain construction, tamper detection, regulatory package generation
MCP command/resource architecture: Tool design for LLM consumers, structured error types, precondition documentation

FDE Skills
The governance conversation: Ability to translate "we need auditability" from a risk/compliance stakeholder into a specific event store deployment recommendation within 48 hours
Enterprise stack translation: Mapping your PostgreSQL implementation to Marten/Wolverine (.NET) and EventStoreDB for clients who already have a stack preference
The one-way door conversation: Knowing how to communicate the migration complexity and long-term commitment of adopting event sourcing, so clients make the decision with accurate information
SLO-based architecture: Designing systems to explicit performance contracts rather than "as fast as possible" — the foundation of production-grade FDE work

The Week Standard
By end of this week, you must be able to demonstrate: "Show me the complete decision history of application ID X" — from first event to final decision, with every AI agent action, every compliance check, every human review, all causal links intact, temporal query to any point in the lifecycle, and cryptographic integrity verification. If you cannot run this demonstration in under 60 seconds, the week is not complete.

Reading Material
An empirical characterization of event sourced systems and their schema evolution — Lessons from industry 

Phase 0 — Domain Reconnaissance (Day 1, Morning)
Event sourcing is one of the most misunderstood patterns in enterprise software. Most engineers who say they have used it have used a version of it — usually without optimistic concurrency control, without projection management, without upcasting, and without understanding why any of those things matter. Phase 0 establishes the conceptual precision required to build the Ledger correctly.
Core Concepts — Required Mastery
Event Sourcing vs. Event-Driven Architecture
These are not the same thing. Event-Driven Architecture (EDA) uses events as messages between services — the sender fires and forgets. Event Sourcing uses events as the system's source of truth — the events ARE the database. Your system today (agent activity tracing component callbacks, the Automaton Auditor's verdict stream) is EDA. The Ledger is event sourcing. The distinction matters because EDA events can be dropped or lost; event store entries never can. Study: Confluent's "Future of AI Agents is Event-Driven" (2025) and contrast with Greg Young's "CQRS and Event Sourcing" talks.
Aggregate Boundaries & Domain Events
An aggregate is a consistency boundary — a cluster of domain objects that must be mutated atomically. An event is the record of a fact that happened to an aggregate. The critical rule: aggregates communicate only through events, never through direct method calls. In the AI era, each AI agent is a natural aggregate boundary: its decisions are facts, recorded as events, never mutated. Study: Vernon's "Implementing Domain-Driven Design", Chapter 10 on aggregates.
CQRS — Command Query Responsibility Segregation
Write operations (Commands) and read operations (Queries) are handled by separate models. Commands append events to streams. Queries read from projections built from those events. The separation enables: independent scaling of reads and writes, multiple read-optimised projections from the same event stream, and the ability to rebuild any read model by replaying events. In the MCP context: MCP Tools are Commands; MCP Resources are Queries against projections.
Optimistic Concurrency Control
In an event store, two processes can simultaneously try to append to the same stream. Without concurrency control, you get split-brain state. The solution: every append operation specifies an expected_version — the stream version it read before making its decision. If the stream's actual version has advanced (because someone else appended), the operation is rejected with a concurrency exception. The caller must reload and retry. This is how the Ledger prevents two AI agents from simultaneously making conflicting decisions. No locks required. No transactions spanning multiple aggregates.
Projections — Inline vs. Async
A projection transforms events into a read model. Inline projections update synchronously in the same transaction as the event write — strong consistency, higher write latency. Async projections update asynchronously via a background daemon — lower write latency, eventual consistency, and the ability to rebuild from scratch by replaying. The Marten library (the enterprise .NET standard for PostgreSQL-backed event stores) calls its async projection runner the "Async Daemon." Python equivalents achieve the same pattern with background asyncio tasks. Study: Marten docs on projection lifecycle; EventStoreDB catch-up subscriptions.
Upcasting — Handling Schema Evolution
In a CRUD system, you run a migration and the data changes. In an event store, the past is immutable. When your event schema evolves, you write an upcaster — a function that transforms old event structures into new ones at read time, without touching the stored events. This is the event sourcing solution to the problem identified by schema evolution analysis tools. In production, upcasters are registered in a chain: v1→v2→v3, applied automatically whenever old events are loaded. An event store without upcasting is an event store that will eventually break under the weight of its own history.
The Outbox Pattern — Guaranteed Event Delivery
The classic distributed systems problem: you append an event to the store AND need to publish it to a message bus (Kafka, Redis Streams, RabbitMQ). If the store write succeeds but the publish fails, your read models and downstream systems are inconsistent. The Outbox Pattern solves this: write events to both the event store and an "outbox" table in the same database transaction. A separate process polls the outbox and publishes reliably. This is how you connect The Ledger to the Polyglot Bridge (Week 10).
The Gas Town Persistent Ledger Pattern
Named for the infrastructure pattern in agentic systems where agent context is lost on process restart. The solution: every agent action is written to the event store as an event before the action is executed. On restart, the agent replays its event stream to reconstruct its context window. This is not just logging — it is the agent's memory backed by the most reliable storage primitive available: an append-only, ACID-compliant, PostgreSQL-backed event stream.


Stack Orientation — Enterprise Tools in 2026
The enterprise market has converged on two primary event store backends. You must understand both even if you implement only one.

TOOL
STACK
BEST FOR
ENTERPRISE ADOPTION
YOUR CHOICE IN THIS CHALLENGE
PostgreSQL + psycopg3
Python (primary)
Single-database architectures; teams already on Postgres; FDE rapid deployment
Extremely high — Postgres is everywhere
PRIMARY — Build the event store schema and all phases using Postgres + asyncpg/psycopg3
EventStoreDB 24.x
Any (HTTP API)
Dedicated high-throughput event stores; persistent subscriptions at scale; native gRPC streaming
Growing — the purpose-built standard
REFERENCE — Know the API; document in DOMAIN_NOTES how your Postgres schema maps to EventStoreDB concepts
Marten 7.x + Wolverine
.NET / C#
Enterprise .NET shops; Async Daemon for projection management; Wolverine for command routing
Dominant in .NET enterprise
CONCEPTUAL — Study the architecture; your Python implementation should mirror the same patterns
Kafka + Kafka Streams
Any
Very-high-throughput event streaming; not a true event store (retention limits)
Ubiquitous in large enterprise
INTEGRATION — Week 10 connects The Ledger to Kafka via the Outbox pattern
Redis Streams
Any
Lower-latency pub/sub; projection fan-out; not durable by default
Common as event bus layer
INTEGRATION — Use Redis Streams for real-time projection update notifications


DOMAIN_NOTES.md — Graded Deliverable
Produce a DOMAIN_NOTES.md before writing any implementation code. It must answer all of the following with specificity, not generality. This document is assessed independently of your code — a candidate who writes excellent code but cannot reason about the tradeoffs is not ready for enterprise event sourcing work.
EDA vs. ES distinction: A component uses callbacks (like LangChain traces) to capture event-like data. Is this Event-Driven Architecture (EDA) or Event Sourcing (ES)? If you redesigned it using The Ledger, what exactly would change in the architecture and what would you gain?
The aggregate question: In the scenario below, you will build four aggregates. Identify one alternative boundary you considered and rejected. What coupling problem does your chosen boundary prevent?
Concurrency in practice: Two AI agents simultaneously process the same loan application and both call append_events with expected_version=3. Trace the exact sequence of operations in your event store. What does the losing agent receive, and what must it do next?
Projection lag and its consequences: Your LoanApplication projection is eventually consistent with a typical lag of 200ms. A loan officer queries "available credit limit" immediately after an agent commits a disbursement event. They see the old limit. What does your system do, and how do you communicate this to the user interface?
The upcasting scenario: The CreditDecisionMade event was defined in 2024 with {application_id, decision, reason}. In 2026 it needs {application_id, decision, reason, model_version, confidence_score, regulatory_basis}. Write the upcaster. What is your inference strategy for historical events that predate model_version?
The Marten Async Daemon parallel: Marten 7.0 introduced distributed projection execution across multiple nodes. Describe how you would achieve the same pattern in your Python implementation. What coordination primitive do you use, and what failure mode does it guard against?

The Scenario — Apex Financial Services
Apex Financial Services is deploying a multi-agent AI platform to process commercial loan applications. Four specialized AI agents collaborate on each application: a CreditAnalysis agent evaluates financial risk, a FraudDetection agent screens for anomalous patterns, a ComplianceAgent verifies regulatory eligibility, and a DecisionOrchestrator synthesises their outputs and produces a final recommendation. Human loan officers review the recommendation and make the final binding decision.
The regulatory environment requires: a complete, immutable audit trail of every AI decision and the data that informed it; the ability to reconstruct the exact state of any application at any point in time for regulatory examination; temporal queries (e.g., "what would the credit decision have been if we had used last month's risk model?"); and cryptographic integrity — any tampering with the audit trail must be detectable. The CTO has mandated that the system must not be modified to add auditability after the fact — auditability must be the architecture, not an annotation.
This is the canonical environment where event sourcing is not just beneficial — it is the only architecture that satisfies the requirements. Your task is to build The Ledger: the event store and its surrounding infrastructure that makes this system governable.

Why This Scenario
Financial services is the highest-density event sourcing environment in enterprise software. Every loan decision, every risk calculation, every compliance check is a regulated event. The same architecture applies directly to any domain where audit trails are non-negotiable: healthcare prior authorisations, government benefit decisions, insurance claim adjudication, and — directly relevant to your work — AI agent decision logs in any enterprise deployment. Master this scenario and you have mastered the pattern for all of them.

The Four Aggregates
AGGREGATE
STREAM ID FORMAT
WHAT IT TRACKS
KEY BUSINESS INVARIANTS
LoanApplication
loan-{application_id}
Full lifecycle of a commercial loan application from submission to decision
Cannot transition from Approved to UnderReview; cannot be approved if compliance check is pending; credit limit cannot exceed agent-assessed maximum
AgentSession
agent-{agent_id}-{session_id}
All actions taken by a specific AI agent instance during a work session, including model version, input data hashes, reasoning trace, and outputs
Every output event must reference a ContextLoaded event; every decision must reference the specific model version that produced it
ComplianceRecord
compliance-{application_id}
Regulatory checks, rule evaluations, and compliance verdicts for each application
Cannot issue a compliance clearance without all mandatory checks; every check must reference the specific regulation version evaluated against
AuditLedger
audit-{entity_type}-{entity_id}
Cross-cutting audit trail linking events across all aggregates for a single business entity
Append-only; no events may be removed; must maintain cross-stream causal ordering via correlation_id chains


The Event Catalogue
These are the events you will implement. The catalogue is intentionally incomplete — identifying the missing events is part of the Phase 1 domain exercise.
EVENT TYPE
AGGREGATE
VERSION
KEY PAYLOAD FIELDS
ApplicationSubmitted
LoanApplication
1
application_id, applicant_id, requested_amount_usd, loan_purpose, submission_channel, submitted_at
CreditAnalysisRequested
LoanApplication
1
application_id, assigned_agent_id, requested_at, priority
CreditAnalysisCompleted
AgentSession
2
application_id, agent_id, session_id, model_version, confidence_score, risk_tier, recommended_limit_usd, analysis_duration_ms, input_data_hash
FraudScreeningCompleted
AgentSession
1
application_id, agent_id, fraud_score, anomaly_flags[], screening_model_version, input_data_hash
ComplianceCheckRequested
ComplianceRecord
1
application_id, regulation_set_version, checks_required[]
ComplianceRulePassed
ComplianceRecord
1
application_id, rule_id, rule_version, evaluation_timestamp, evidence_hash
ComplianceRuleFailed
ComplianceRecord
1
application_id, rule_id, rule_version, failure_reason, remediation_required
DecisionGenerated
LoanApplication
2
application_id, orchestrator_agent_id, recommendation (APPROVE/DECLINE/REFER), confidence_score, contributing_agent_sessions[], decision_basis_summary, model_versions{}
HumanReviewCompleted
LoanApplication
1
application_id, reviewer_id, override (bool), final_decision, override_reason (if override)
ApplicationApproved
LoanApplication
1
application_id, approved_amount_usd, interest_rate, conditions[], approved_by (human_id or "auto"), effective_date
ApplicationDeclined
LoanApplication
1
application_id, decline_reasons[], declined_by, adverse_action_notice_required (bool)
AgentContextLoaded
AgentSession
1
agent_id, session_id, context_source, event_replay_from_position, context_token_count, model_version
AuditIntegrityCheckRun
AuditLedger
1
entity_id, check_timestamp, events_verified_count, integrity_hash, previous_hash (chain)


PHASE 1  ·  The Event Store Core — PostgreSQL Schema & Interface
Build the event store foundation. Everything else is built on this. The schema is not a suggestion — it is the contract that every other component in this program will eventually write to and read from. Please identify and report if there are missing elements that could improve the schema validity in future scenarios. 
Database Schema
Create the following tables. Justify every column in DESIGN.md — columns you cannot justify should not exist.

CREATE TABLE events (
  event_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  stream_id        TEXT NOT NULL,
  stream_position  BIGINT NOT NULL,
  global_position  BIGINT GENERATED ALWAYS AS IDENTITY,
  event_type       TEXT NOT NULL,
  event_version    SMALLINT NOT NULL DEFAULT 1,
  payload          JSONB NOT NULL,
  metadata         JSONB NOT NULL DEFAULT '{}'::jsonb,
  recorded_at      TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
  CONSTRAINT uq_stream_position UNIQUE (stream_id, stream_position)
);

CREATE INDEX idx_events_stream_id ON events (stream_id, stream_position);
CREATE INDEX idx_events_global_pos ON events (global_position);
CREATE INDEX idx_events_type ON events (event_type);
CREATE INDEX idx_events_recorded ON events (recorded_at);

CREATE TABLE event_streams (
  stream_id        TEXT PRIMARY KEY,
  aggregate_type   TEXT NOT NULL,
  current_version  BIGINT NOT NULL DEFAULT 0,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  archived_at      TIMESTAMPTZ,
  metadata         JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE projection_checkpoints (
  projection_name  TEXT PRIMARY KEY,
  last_position    BIGINT NOT NULL DEFAULT 0,
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE outbox (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id         UUID NOT NULL REFERENCES events(event_id),
  destination      TEXT NOT NULL,
  payload          JSONB NOT NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  published_at     TIMESTAMPTZ,
  attempts         SMALLINT NOT NULL DEFAULT 0
);

Core Python Interface
Implement EventStore as an async Python class. The interface is fixed — implementation is yours.

class EventStore:
    async def append(
        self,
        stream_id: str,
        events: list[BaseEvent],
        expected_version: int,          # -1 = new stream; N = exact version required
        correlation_id: str | None = None,
        causation_id:   str | None = None,
    ) -> int:                            # returns new stream version
        """
        Atomically appends events to stream_id.
        Raises OptimisticConcurrencyError if stream version != expected_version.
        Writes to outbox in same transaction.
        """

    async def load_stream(
        self,
        stream_id: str,
        from_position: int = 0,
        to_position:   int | None = None,
    ) -> list[StoredEvent]:             # events in stream order, upcasted

    async def load_all(
        self,
        from_global_position: int = 0,
        event_types: list[str] | None = None,
        batch_size: int = 500,
    ) -> AsyncIterator[StoredEvent]:   # async generator, efficient for replay

    async def stream_version(self, stream_id: str) -> int:
    async def archive_stream(self, stream_id: str) -> None:
    async def get_stream_metadata(self, stream_id: str) -> StreamMetadata:

Optimistic Concurrency — The Double-Decision Test
This is the most critical test in Phase 1. Two AI agents simultaneously attempt to append a CreditAnalysisCompleted event to the same loan application stream. Both read the stream at version 3 and pass expected_version=3 to their append call. Exactly one must succeed. The other must receive OptimisticConcurrencyError and retry after reloading the stream.
Implement a test that spawns two concurrent asyncio tasks doing this. The test must assert: (a) total events appended to the stream = 4 (not 5), (b) the winning task's event has stream_position=4, (c) the losing task's OptimisticConcurrencyError is raised, not silently swallowed.
Why This Matters
In the Apex loan scenario, this test represents two fraud-detection agents simultaneously flagging the same application. Without optimistic concurrency, both flags are applied and the application's state becomes inconsistent — no one knows which fraud score is authoritative. With it, one agent's decision wins; the other must reload and see whether its analysis is still relevant. This is not an edge case — at 1,000 applications/hour with 4 agents each, concurrency collisions happen constantly.

PHASE 2  ·  Domain Logic — Aggregates, Commands & Business Rules
Implement the domain logic for LoanApplication and AgentSession. The pattern: command received → aggregate state reconstructed by replaying events → business rules validated → new events appended.
The Command Handler Pattern
# Every command handler follows this exact structure:
async def handle_credit_analysis_completed(
    cmd: CreditAnalysisCompletedCommand,
    store: EventStore,
) -> None:
    # 1. Reconstruct current aggregate state from event history
    app = await LoanApplicationAggregate.load(store, cmd.application_id)
    agent = await AgentSessionAggregate.load(store, cmd.agent_id, cmd.session_id)

    # 2. Validate — all business rules checked BEFORE any state change
    app.assert_awaiting_credit_analysis()
    agent.assert_context_loaded()                    # Gas Town pattern
    agent.assert_model_version_current(cmd.model_version)

    # 3. Determine new events — pure logic, no I/O
    new_events = [
        CreditAnalysisCompleted(
            application_id = cmd.application_id,
            agent_id       = cmd.agent_id,
            session_id     = cmd.session_id,
            model_version  = cmd.model_version,
            confidence_score = cmd.confidence_score,
            risk_tier      = cmd.risk_tier,
            recommended_limit_usd = cmd.recommended_limit_usd,
            analysis_duration_ms  = cmd.duration_ms,
            input_data_hash = hash_inputs(cmd.input_data),
        )
    ]

    # 4. Append atomically — optimistic concurrency enforced by store
    await store.append(
        stream_id        = f"loan-{cmd.application_id}",
        events           = new_events,
        expected_version = app.version,
        correlation_id   = cmd.correlation_id,
        causation_id     = cmd.causation_id,
    )

Business Rules to Enforce
The following rules must be enforced in the aggregate domain logic, not in the API layer. A rule that is only checked in a request handler is not a business rule — it is a UI validation.
Application state machine: Valid transitions only: Submitted → AwaitingAnalysis → AnalysisComplete → ComplianceReview → PendingDecision → ApprovedPendingHuman / DeclinedPendingHuman → FinalApproved / FinalDeclined. Any out-of-order transition raises DomainError.
Agent context requirement (Gas Town): An AgentSession aggregate MUST have an AgentContextLoaded event as its first event before any decision event can be appended. This enforces the persistent ledger pattern — no agent may make a decision without first declaring its context source.
Model version locking: Once a CreditAnalysisCompleted event is appended for an application, no further CreditAnalysisCompleted events may be appended for the same application unless the first was superseded by a HumanReviewOverride. This prevents analysis churn.
Confidence floor: A DecisionGenerated event with confidence_score < 0.6 must set recommendation = "REFER" regardless of the orchestrator's analysis. This is a regulatory requirement, enforced in the aggregate.
Compliance dependency: An ApplicationApproved event cannot be appended unless all ComplianceRulePassed events for the application's required checks are present in the ComplianceRecord stream. The LoanApplication aggregate must hold a reference to check this.
Causal chain enforcement: Every DecisionGenerated event's contributing_agent_sessions[] list must reference only AgentSession stream IDs that contain a decision event for this application_id. An orchestrator that references sessions that never processed this application must be rejected.

Aggregate State Reconstruction
Each aggregate must implement a load() classmethod that replays its event stream and applies each event to build current state. The apply pattern must be explicit — one method per event type:
class LoanApplicationAggregate:
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
        self.applicant_id = event.payload["applicant_id"]
        self.requested_amount = event.payload["requested_amount_usd"]

    def _on_ApplicationApproved(self, event: StoredEvent) -> None:
        self.state = ApplicationState.FINAL_APPROVED
        self.approved_amount = event.payload["approved_amount_usd"]


PHASE 3  ·  Projections — CQRS Read Models & Async Daemon 
Projections are the read side of CQRS. They subscribe to the event stream and maintain read-optimised views that can be queried without loading and replaying aggregate streams. Build three projections and the async daemon that keeps them current.
The Async Projection Daemon
The daemon is a background asyncio task that continuously polls the events table from the last processed global_position, processes new events through registered projections, and updates projection_checkpoints. It must be fault-tolerant: if a projection handler fails, the daemon must log the error, skip the offending event (with configurable retry count), and continue. A daemon that crashes on a bad event is a production incident.
class ProjectionDaemon:
    def __init__(self, store: EventStore, projections: list[Projection]):
        self._store = store
        self._projections = {p.name: p for p in projections}
        self._running = False

    async def run_forever(self, poll_interval_ms: int = 100) -> None:
        self._running = True
        while self._running:
            await self._process_batch()
            await asyncio.sleep(poll_interval_ms / 1000)

    async def _process_batch(self) -> None:
        # Load lowest checkpoint across all projections
        # Load events from that position in batches
        # For each event, route to subscribed projections
        # Update checkpoints after each successful batch
        # Expose lag metric: global_position - last_processed_position
        ...

Required Projections
Projection 1: ApplicationSummary
A read-optimised view of every loan application's current state. Stored as a Postgres table (one row per application). Updated inline by the daemon as new events arrive.
Table schema:
application_id, state, applicant_id,
requested_amount_usd, approved_amount_usd,
risk_tier, fraud_score,
compliance_status, decision,
agent_sessions_completed[],
last_event_type, last_event_at,
human_reviewer_id, final_decision_at

Projection 2: AgentPerformanceLedger
Aggregated performance metrics per AI agent model version. Enables the question: "Has agent v2.3 been making systematically different decisions than v2.2?"
Table schema:
agent_id, model_version,
analyses_completed, decisions_generated,
avg_confidence_score, avg_duration_ms,
approve_rate, decline_rate, refer_rate,
human_override_rate,
first_seen_at, last_seen_at
Projection 3: ComplianceAuditView (Critical)
This projection is the regulatory read model — the view that a compliance officer or regulator queries when examining an application. It must be complete (every compliance event), traceable (every rule references its regulation version), and temporally queryable (state at any past timestamp).
Unlike the other projections, the ComplianceAuditView must support the temporal query interface: get_state_at(application_id, timestamp) → ComplianceAuditView. This requires a snapshot strategy you must implement and justify in DESIGN.md.
get_current_compliance(application_id) → full compliance record with all checks, verdicts, and regulation versions
get_compliance_at(application_id, timestamp) → compliance state as it existed at a specific moment (regulatory time-travel)
get_projection_lag() → milliseconds between latest event in store and latest event this projection has processed — must be exposed as a metric
rebuild_from_scratch() → truncate projection table and replay all events from position 0 — must complete without downtime to live reads

Projection Lag — The Non-Negotiable Metric
The Lag Contract
Your ApplicationSummary projection must maintain a lag of under 500ms in normal operation. Your ComplianceAuditView projection may lag up to 2 seconds. These are not arbitrary numbers — they are service-level objectives (SLOs) you define in your DESIGN.md and demonstrate in testing. A projection system with no lag measurement is not production-ready. Your daemon must expose get_lag() for every projection it manages, and your test suite must assert that lag stays within bounds under a simulated load of 50 concurrent command handlers.

PHASE 4  ·  Upcasting, Integrity & The Gas Town Memory Pattern
4A — Upcaster Registry
Implement a centralized UpcasterRegistry that automatically applies version migrations whenever old events are loaded from the store. The event loading path must call the registry transparently — callers never manually invoke upcasters.
class UpcasterRegistry:
    def __init__(self):
        self._upcasters: dict[tuple[str, int], Callable] = {}

    def register(self, event_type: str, from_version: int):
        """Decorator. Registers fn as upcaster from event_type@from_version."""
        def decorator(fn: Callable[[dict], dict]) -> Callable:
            self._upcasters[(event_type, from_version)] = fn
            return fn
        return decorator

    def upcast(self, event: StoredEvent) -> StoredEvent:
        """Apply all registered upcasters for this event type in version order."""
        current = event
        v = event.event_version
        while (event.event_type, v) in self._upcasters:
            new_payload = self._upcasters[(event.event_type, v)](current.payload)
            current = current.with_payload(new_payload, version=v + 1)
            v += 1
        return current

# Usage:
registry = UpcasterRegistry()

@registry.register("CreditAnalysisCompleted", from_version=1)
def upcast_credit_v1_to_v2(payload: dict) -> dict:
    return {
        **payload,
        "model_version": "legacy-pre-2026",   # inference for historical events
        "confidence_score": None,              # genuinely unknown — do not fabricate
    }

Implement upcasters for the following events and justify your inference strategy for missing historical fields in DESIGN.md:
CreditAnalysisCompleted v1→v2: Add model_version (inferred from recorded_at timestamp), confidence_score (null — genuinely unknown; document why fabrication would be worse than null), regulatory_basis (infer from rule versions active at recorded_at date).
DecisionGenerated v1→v2: Add model_versions{} dict (reconstruct from contributing_agent_sessions by loading each session's AgentContextLoaded event — this requires a store lookup; document the performance implication).

The Immutability Test
Your test suite must include a test that: (1) directly queries the events table in Postgres to get the raw stored payload of a v1 event, (2) loads the same event through your EventStore.load_stream() and verifies it is upcasted to v2, (3) directly queries the events table again and verifies the raw stored payload is UNCHANGED. Any system where upcasting touches the stored events has broken the core guarantee of event sourcing. This test is mandatory and will be run during assessment.
4B — Cryptographic Audit Chain
Regulatory-grade audit trails require tamper evidence. Implement a hash chain over the event log for the AuditLedger aggregate. Each AuditIntegrityCheckRun event records a hash of all preceding events plus the previous integrity hash, forming a blockchain-style chain. Any post-hoc modification of events breaks the chain.
async def run_integrity_check(
    store: EventStore,
    entity_type: str,
    entity_id: str,
) -> IntegrityCheckResult:
    """
    1. Load all events for the entity's primary stream
    2. Load the last AuditIntegrityCheckRun event (if any)
    3. Hash the payloads of all events since the last check
    4. Verify hash chain: new_hash = sha256(previous_hash + event_hashes)
    5. Append new AuditIntegrityCheckRun event to audit-{entity_type}-{entity_id} stream
    6. Return result with: events_verified, chain_valid (bool), tamper_detected (bool)
    """

4C — The Gas Town Agent Memory Pattern
Implement the pattern that prevents the catastrophic memory loss described in the program materials. An AI agent that crashes mid-session must be able to restart and reconstruct its exact context from the event store, then continue where it left off without repeating completed work.
async def reconstruct_agent_context(
    store: EventStore,
    agent_id: str,
    session_id: str,
    token_budget: int = 8000,
) -> AgentContext:
    """
    1. Load full AgentSession stream for agent_id + session_id
    2. Identify: last completed action, pending work items, current application state
    3. Summarise old events into prose (token-efficient)
    4. Preserve verbatim: last 3 events, any PENDING or ERROR state events
    5. Return: AgentContext with context_text, last_event_position,
               pending_work[], session_health_status

    CRITICAL: if the agent's last event was a partial decision (no corresponding
    completion event), flag the context as NEEDS_RECONCILIATION — the agent
    must resolve the partial state before proceeding.
    """

Test this pattern with a simulated crash: start an agent session, append 5 events, then call reconstruct_agent_context() without the in-memory agent object. Verify that the reconstructed context contains enough information for the agent to continue correctly.

PHASE 5  ·  MCP Server — Exposing The Ledger as Enterprise Infrastructure 
The MCP server is the interface between The Ledger and any AI agent or enterprise system that needs to interact with it. Tools (Commands) write events; Resources (Queries) read from projections. This is structural CQRS — the MCP specification naturally implements the read/write separation.
MCP Tools — The Command Side
TOOL NAME
COMMAND IT EXECUTES
CRITICAL VALIDATION
RETURN VALUE
submit_application
ApplicationSubmitted
Schema validation via Pydantic; duplicate application_id check
stream_id, initial_version
record_credit_analysis
CreditAnalysisCompleted
agent_id must have active AgentSession with context loaded; optimistic concurrency on loan stream
event_id, new_stream_version
record_fraud_screening
FraudScreeningCompleted
Same agent session validation; fraud_score must be 0.0–1.0
event_id, new_stream_version
record_compliance_check
ComplianceRulePassed / ComplianceRuleFailed
rule_id must exist in active regulation_set_version
check_id, compliance_status
generate_decision
DecisionGenerated
All required analyses must be present; confidence floor enforcement
decision_id, recommendation
record_human_review
HumanReviewCompleted
reviewer_id authentication; if override=True, override_reason required
final_decision, application_state
start_agent_session
AgentContextLoaded
Gas Town: required before any agent decision tools; writes context source and token count
session_id, context_position
run_integrity_check
AuditIntegrityCheckRun
Can only be called by compliance role; rate-limited to 1/minute per entity
check_result, chain_valid


MCP Resources — The Query Side
Resources expose projections. They must never load aggregate streams — all reads must come from projections. A resource that replays events on every query is an anti-pattern that will not scale.
RESOURCE URI
PROJECTION SOURCE
SUPPORTS TEMPORAL QUERY?
SLO
ledger://applications/{id}
ApplicationSummary
No — current state only
p99 < 50ms
ledger://applications/{id}/compliance
ComplianceAuditView
Yes — ?as_of=timestamp
p99 < 200ms
ledger://applications/{id}/audit-trail
AuditLedger stream (direct load — justified exception)
Yes — ?from=&to= range
p99 < 500ms
ledger://agents/{id}/performance
AgentPerformanceLedger
No — current metrics only
p99 < 50ms
ledger://agents/{id}/sessions/{session_id}
AgentSession stream (direct load)
Yes — full replay capability
p99 < 300ms
ledger://ledger/health
ProjectionDaemon.get_all_lags()
No
p99 < 10ms — this is the watchdog endpoint


Tool Interface Design for LLM Consumption
Tools and resources are consumed by AI agents, not humans. The description and parameter schema of each tool determines whether the consuming LLM uses it correctly — this is API design for a non-human consumer. Two requirements that most engineers miss:
Precondition documentation in the tool description: "This tool requires an active agent session created by start_agent_session. Calling without an active session will return a PreconditionFailed error." An LLM that does not know this precondition will repeatedly fail and retry. The description is the only contract the LLM has.
Structured error types, not messages: Errors returned by tools must be typed objects: {error_type: "OptimisticConcurrencyError", message: "...", stream_id: "...", expected_version: 3, actual_version: 5, suggested_action: "reload_stream_and_retry"}. An LLM that receives an unstructured error message cannot reason about what to do. A typed error with suggested_action enables autonomous recovery.

The MCP Integration Test
Your MCP server must pass this integration test: start a fresh Ledger instance, then drive a complete loan application lifecycle — from ApplicationSubmitted through FinalApproved — using only MCP tool calls. No direct Python function calls. The test simulates what a real AI agent would do: it calls start_agent_session, then record_credit_analysis, then generate_decision, then record_human_review, then queries the compliance audit view to verify the complete trace is present. If any step requires a workaround outside the MCP interface, the interface has a design flaw.

PHASE 6 (BONUS)  ·  What-If Projections & Regulatory Time Travel
This phase is required for Score 5 and is the discriminator for trainees with genuine event sourcing experience. It is challenging and takes a full day. Attempt it only after Phases 1–5 are solid.
The What-If Projector
The Apex compliance team needs to run counterfactual scenarios: "What would the decision have been if we had used the March risk model instead of the February risk model?" This requires replaying application history with a substituted event — a counterfactual — injected at the point of the original credit analysis.
async def run_what_if(
    store: EventStore,
    application_id: str,
    branch_at_event_type: str,            # e.g. "CreditAnalysisCompleted"
    counterfactual_events: list[BaseEvent],  # events to inject instead of real ones
    projections: list[Projection],        # projections to evaluate under the scenario
) -> WhatIfResult:
    """
    1. Load all events for the application stream up to the branch point
    2. At the branch point, inject counterfactual_events instead of real events
    3. Continue replaying real events that are causally INDEPENDENT of the branch
    4. Skip real events that are causally DEPENDENT on the branched events
    5. Apply all events (pre-branch real + counterfactual + post-branch independent)
       to each projection
    6. Return: {real_outcome, counterfactual_outcome, divergence_events[]}

    NEVER writes counterfactual events to the real store.
    Causal dependency: an event is dependent if its causation_id traces
    back to an event at or after the branch point.
    """

Demonstrate with the specific scenario: "What would the final decision have been if the credit analysis had returned risk_tier='HIGH' instead of 'MEDIUM'?" Your what-if projector must produce a materially different ApplicationSummary outcome — demonstrating that business rule enforcement cascades correctly through the counterfactual.

Regulatory Examination Package
Implement a generate_regulatory_package(application_id, examination_date) function that produces a complete, self-contained examination package containing:
The complete event stream for the application, in order, with full payloads.
The state of every projection as it existed at examination_date.
The audit chain integrity verification result.
A human-readable narrative of the application lifecycle, generated by replaying events and constructing a plain-English summary (one sentence per significant event).
The model versions, confidence scores, and input data hashes for every AI agent that participated in the decision.
The package must be a self-contained JSON file that a regulator can verify against the database independently — they should not need to trust your system to validate that the package is accurate.

DESIGN.md — Required Sections
This document is assessed with equal weight to the code. The principle: architecture is about tradeoffs. A decision without a tradeoff analysis is not an architectural decision — it is a default. Six required sections:

Aggregate boundary justification: Why is ComplianceRecord a separate aggregate from LoanApplication? What would couple if you merged them? Trace the coupling to a specific failure mode under concurrent write scenarios.
Projection strategy: For each projection, justify: Inline vs. Async, and the SLO commitment. For the ComplianceAuditView temporal query, justify your snapshot strategy (event-count trigger, time trigger, or manual) and describe snapshot invalidation logic.
Concurrency analysis: Under peak load (100 concurrent applications, 4 agents each), how many OptimisticConcurrencyErrors do you expect per minute on the loan-{id} streams? What is the retry strategy and what is the maximum retry budget before you return a failure to the caller?
Upcasting inference decisions: For every inferred field in your upcasters, quantify the likely error rate and the downstream consequence of an incorrect inference. When would you choose null over an inference?
EventStoreDB comparison: Map your PostgreSQL schema to EventStoreDB concepts: streams → stream IDs, your load_all() → EventStoreDB $all stream subscription, your ProjectionDaemon → EventStoreDB persistent subscriptions. What does EventStoreDB give you that your implementation must work harder to achieve?
What you would do differently: Name the single most significant architectural decision you would reconsider with another full day. This section is the most important — it shows whether you can distinguish between "what I built" and "what the best version of this would be."

Deliverables
Interim — Sunday March 22, 03:00 UTC
GitHub Code:
src/schema.sql — PostgreSQL schema: events, event_streams, projection_checkpoints, outbox tables with all indexes and constraints
src/event_store.py — EventStore async class with append, load_stream, load_all, stream_version, archive_stream, get_stream_metadata; optimistic concurrency enforced via expected_version
src/models/events.py — Pydantic models for all event types in the Event Catalogue (BaseEvent, StoredEvent, StreamMetadata) plus custom exceptions (OptimisticConcurrencyError, DomainError)
src/aggregates/loan_application.py — LoanApplicationAggregate with state machine, event replay via load(), and _apply handlers for all loan lifecycle events
src/aggregates/agent_session.py — AgentSessionAggregate with Gas Town context enforcement and model version tracking
src/commands/handlers.py — Command handlers following the load → validate → determine → append pattern (at minimum: handle_credit_analysis_completed, handle_submit_application)
tests/test_concurrency.py — Double-decision concurrency test: two concurrent asyncio tasks appending to the same stream at expected_version=3; asserts exactly one succeeds, one raises OptimisticConcurrencyError, and total stream length = 4
pyproject.toml with locked deps (uv)
README.md — how to install, run migrations, and execute the test suite
Single PDF Report containing:
DOMAIN_NOTES.md content (complete, as graded deliverable)
Architecture diagram showing event store schema, aggregate boundaries, and command flow
Progress summary: what is working (Phase 1 + Phase 2), what is in progress
Concurrency test results: screenshot or log output of the double-decision test passing
Known gaps and plan for final submission
Final — Thursday March 26, 03:00 UTC
GitHub Code (full system):
Phase 1 — Event Store Core:
src/schema.sql — Full PostgreSQL schema with all tables, indexes, and constraints
src/event_store.py — Complete EventStore async class with all interface methods, outbox writes in same transaction, stream archival support
src/models/events.py — All Pydantic models: event types, stored event wrapper, stream metadata, error types
Phase 2 — Domain Logic:
src/aggregates/loan_application.py — LoanApplicationAggregate with full state machine (Submitted → AwaitingAnalysis → AnalysisComplete → ComplianceReview → PendingDecision → ApprovedPendingHuman / DeclinedPendingHuman → FinalApproved / FinalDeclined), all 6 business rules enforced
src/aggregates/agent_session.py — AgentSessionAggregate with Gas Town context enforcement, model version locking
src/aggregates/compliance_record.py — ComplianceRecordAggregate with mandatory check tracking and regulation version references
src/aggregates/audit_ledger.py — AuditLedgerAggregate with append-only enforcement and cross-stream causal ordering
src/commands/handlers.py — All command handlers: submit_application, credit_analysis_completed, fraud_screening_completed, compliance_check, generate_decision, human_review_completed, start_agent_session
Phase 3 — Projections & Async Daemon:
src/projections/daemon.py — ProjectionDaemon with fault-tolerant batch processing, per-projection checkpoint management, configurable retry, and get_lag() per projection
src/projections/application_summary.py — ApplicationSummary projection (one row per application, current state)
src/projections/agent_performance.py — AgentPerformanceLedger projection (metrics per agent model version)
src/projections/compliance_audit.py — ComplianceAuditView projection with temporal query support (get_compliance_at(application_id, timestamp)), snapshot strategy, and rebuild_from_scratch()
Phase 4 — Upcasting, Integrity & Gas Town:
src/upcasting/registry.py — UpcasterRegistry with automatic version chain application on event load
src/upcasting/upcasters.py — Registered upcasters: CreditAnalysisCompleted v1→v2, DecisionGenerated v1→v2, with inference strategies documented
src/integrity/audit_chain.py — run_integrity_check(): SHA-256 hash chain construction, tamper detection, chain verification
src/integrity/gas_town.py — reconstruct_agent_context(): agent memory reconstruction from event stream with token budget, NEEDS_RECONCILIATION detection
Phase 5 — MCP Server:
src/mcp/server.py — MCP server entry point
src/mcp/tools.py — 8 MCP tools (command side): submit_application, record_credit_analysis, record_fraud_screening, record_compliance_check, generate_decision, record_human_review, start_agent_session, run_integrity_check; all with structured error types and precondition documentation in tool descriptions
src/mcp/resources.py — 6 MCP resources (query side): ledger://applications/{id}, ledger://applications/{id}/compliance, ledger://applications/{id}/audit-trail, ledger://agents/{id}/performance, ledger://agents/{id}/sessions/{session_id}, ledger://ledger/health; all reading from projections (no stream replays except justified exceptions)
Phase 6 (Bonus):
src/what_if/projector.py — run_what_if(): counterfactual event injection with causal dependency filtering, never writes to real store
src/regulatory/package.py — generate_regulatory_package(): self-contained JSON examination package with event stream, projection states at examination date, integrity verification, human-readable narrative, and agent model metadata
Tests:
tests/test_concurrency.py — Double-decision test (two concurrent appends, exactly one succeeds)
tests/test_upcasting.py — Immutability test: v1 event stored, loaded as v2 via upcaster, raw DB payload confirmed unchanged
tests/test_projections.py — Projection lag SLO tests under simulated load of 50 concurrent command handlers; rebuild_from_scratch test
tests/test_gas_town.py — Simulated crash recovery: 5 events appended, reconstruct_agent_context() called without in-memory agent, verify reconstructed context is sufficient to continue
tests/test_mcp_lifecycle.py — Full loan application lifecycle driven entirely through MCP tool calls: start_agent_session → record_credit_analysis → record_fraud_screening → record_compliance_check → generate_decision → record_human_review → query ledger://applications/{id}/compliance to verify complete trace
pyproject.toml with locked deps (uv)
README.md — Full setup instructions: database provisioning, migration, running all phases, MCP server startup, and query examples


Single PDF Report containing:
DOMAIN_NOTES.md content (complete, finalized)
DESIGN.md content (complete, finalized)
Architecture diagram: event store schema, aggregate boundaries, projection data flow, MCP tool/resource mapping
Concurrency & SLO analysis: double-decision test results, projection lag measurements under load, retry budget analysis
Upcasting & integrity results: immutability test output, hash chain verification output, tamper detection demonstration
MCP lifecycle test results: full loan application trace from ApplicationSubmitted through FinalApproved via MCP tools only
Bonus results (if attempted): what-if counterfactual outcome comparison, regulatory package sample output
Limitations & reflection: what the implementation does not handle, what you would change with more time
Video Demo (max 6 min):
Minutes 1–3 (Required):
Step 1 — The Week Standard: Run "Show me the complete decision history of application ID X" end-to-end. Show full event stream, all agent actions, compliance checks, human review, causal links, and cryptographic integrity verification. Time it — must complete in under 60 seconds.
Step 2 — Concurrency Under Pressure: Run the double-decision test live. Show two agents colliding on the same stream, one succeeding, one receiving OptimisticConcurrencyError and retrying.
Step 3 — Temporal Compliance Query: Query ledger://applications/{id}/compliance?as_of={timestamp} for a past point in time. Show the compliance state as it existed at that moment, distinct from the current state.
Minutes 4–6 (Mastery):
Step 4 — Upcasting & Immutability: Load a v1 event through the store, show it arrives as v2. Query the raw database row and show the stored payload is unchanged.
Step 5 — Gas Town Recovery: Start an agent session, append several events, simulate a crash (kill the process). Call reconstruct_agent_context() and show the agent can resume with correct state.
Step 6 — What-If Counterfactual (Bonus): Run a what-if scenario substituting a HIGH risk tier for MEDIUM. Show the cascading effect on the final decision through business rule enforcement.

Assessment Rubric
Score 3 = functional and demonstrates understanding. Score 5 = production-ready, would deploy to a real enterprise client. Scores 4 and 5 require demonstrated understanding in DESIGN.md, not just working code.

CRITERION
1
2
3
4
5
Event Store Core & Concurrency
Schema present; no concurrency control
Append works; expected_version not enforced
All interface methods; concurrency enforced; double-decision test passes
Outbox pattern; archive support; all edge cases; concurrent load test passes
Above + DESIGN.md justifies every schema column; retry strategy documented with error rate estimate
Domain Logic & Business Rules
One aggregate; no state machine
State machine present; some rules missing
Both aggregates; all 6 business rules enforced
Causal chain enforcement; Gas Town pattern; model version locking
Above + counterfactual command testing; all invariants tested under concurrent scenarios
Projection Daemon & CQRS
No projections or direct stream reads only
One projection; no lag metric
All 3 projections; lag metric exposed; daemon fault-tolerant
SLO tests passing; rebuild-from-scratch without downtime; temporal query on ComplianceAuditView
Above + snapshot invalidation; distributed daemon analysis in DESIGN.md
Upcasting & Integrity
No upcasting; store mutated on upcast
Upcaster exists; chain not automatic
Auto-upcasting via registry; immutability test passes
Both upcasters; inference justified; null vs. fabrication reasoning present
Above + hash chain integrity; generate_regulatory_package working; chain break detection
MCP Server — Tool Design
No MCP server
Tools present; error types unstructured
All 8 tools; structured errors; preconditions documented
Resources from projections (no stream reads in resources); SLOs met
Above + full lifecycle integration test via MCP only; LLM-consumption preconditions in all tool descriptions
DESIGN.md — Architectural Reasoning
Not present
Describes what was built; no tradeoff analysis
All 6 sections; tradeoffs identified
Quantitative analysis (error rates, lag SLOs, retry budgets)
"What I would do differently" shows genuine reflection; identifies the thing the implementation got wrong
BONUS — What-If & Regulatory Package
(Not attempted)
(Not attempted)
What-if projection working on test scenario
Counterfactual produces materially different outcome; causal dependency filtering correct
Above + regulatory package is independently verifiable; narrative generation coherent







TRP1  ·  THE LEDGER  ·  ARC 5: INTEGRATION & PROTOCOL ARCHITECTURE
Event Sourcing
Practitioner Manual
Complete reference for knowledge, skills, behaviours, and competencies — covering conceptual foundations, enterprise tool stack, schema design, query patterns, solution architectures, and guidance for novice and experienced practitioners.



AUDIENCE
Audience — onboarding and upskilling companion
Enterprise candidates — pre-engagement reference
CONTENTS
I  ·  Conceptual Landscape & Pattern Map
II  ·  Deep Jargon Glossary (7 clusters, 18 terms)
III  ·  KSBC Framework (Knowledge, Skills, Behaviours, Competencies)
IV  ·  Event Schema Design Reference
V  ·  Query Pattern Reference (8 canonical queries)
VI  ·  Solution Architecture Reference (4 patterns)
VII  ·  Guidance for Mastery: Self-Assessment and Advanced Concepts




TRP1 FDE Program  ·  March 2026  ·  Confidential Training Resource

  HOW TO USE THIS MANUAL  
A guide to getting value from this document quickly
If you are preparing for Arc 5


Start with Part I (Conceptual Map) to verify your mental model is precise. Then read Part II (Jargon Glossary) — specifically the Notes on each term. Read Part VII (Guidance for Mastery) before the week begins so the diagnostic moments are familiar when they appear.


If you are new to event sourcing


Read Part I completely before starting Phase 0 of the challenge. Use Part II as a reference during implementation — look up terms when you encounter them. Part III (KSBC) is your self-assessment framework: be honest about where you are.


If you are an experienced ES practitioner
Skim Part I to verify alignment; focus on Part II Clusters D and E (enterprise and AI-era patterns). Part VI (Architectures) contains the AI multi-agent coordination pattern and the greenfield decision framework — these are the most relevant to your current work. Part VII Checkpoint 5-8 describes what to probe in your own design.


If you are preparing for an enterprise ES role
Parts IV and V (Schema Reference and Query Patterns) are your technical reference. Part VI (Architectures 1-4) contains the design templates. The KSBC Level 3 (Principal) descriptors in Part III describe what the role requires.
If you are using this as a reference during a client engagement
Part VI Architecture 4 (Greenfield Decision Framework) is the advisory framework. The callout "The One-Way Door Conversation" in Part VI is the single most important piece of client communication guidance in this document.


A note on the Notes throughout this manual: they are written for all practitioners. Understanding why a concept is commonly misunderstood — and how to recognise when you have misunderstood it — is itself a form of expertise. The most common misconceptions in Part VII.4 are the result of accurate-but-incomplete mental models. Reading them is inoculation.

  PART I
The Conceptual Landscape
Event Sourcing, its relatives, and why most engineers confuse them
1.1  The Family of Patterns — A Precise Map
Event sourcing belongs to a family of related architectural patterns. A common failure is treating them as interchangeable or as a stack that is always used together. They are not. Each pattern solves a different problem, and they combine in specific ways for specific reasons. Your first job is to ensure you have a precise mental model of the relationships before any implementation begins.

PATTERN
CORE PROBLEM SOLVED
PRIMARY PRIMITIVE
RELATIONSHIP TO ES
COMMON CONFUSION
Event Sourcing (ES)
How do we store state so that history is never lost and any past state is reproducible?
Immutable, append-only event stream as the source of truth
— (the subject of this manual)
Confused with EDA because both use "events"
Event-Driven Architecture (EDA)
How do services communicate without tight coupling?
Events as messages passed between services (can be dropped, deduplicated, lost)
Complementary: an event-sourced system can publish domain events to an EDA bus; they are not the same
You might think EDA = ES because both involve "events flowing"


CQRS
How do we scale reads and writes independently when their requirements diverge?
Separate command (write) model and query (read) model
Frequently paired with ES: commands append events, queries read projections; but CQRS does not require ES and ES does not require CQRS
Practitioners often implement both together and cannot explain which part is which


Domain-Driven Design (DDD)
How do we model complex business domains so code reflects business language?
Bounded contexts, aggregates, domain events, ubiquitous language
ES implements the persistence layer for DDD aggregates using their domain events; DDD is design methodology, ES is persistence strategy
You might think DDD is required for ES; it is not — ES is useful without DDD


Saga / Process Manager
How do we coordinate multi-step business processes that span multiple aggregates or services?
Long-running process that reacts to events and issues commands
Sagas are implemented on top of ES: they listen to events in the store and produce commands; they are not part of the store itself
Commonly conflating the saga coordinator with the event store


Outbox Pattern
How do we guarantee that a state change and an external notification happen atomically?
Write to the outbox table in the same DB transaction as the state change; poll outbox for delivery
Used to reliably publish ES domain events to external systems (Kafka, RabbitMQ); solves the dual-write problem
Skipping the outbox often leads to projections missing events under load


CRDT (Conflict-free Replicated Data Type)
How do we merge state from multiple nodes without coordination?
Mathematically merge-safe data structures
Alternative to optimistic concurrency — relevant in distributed edge deployments; not a substitute for an event store in high-integrity scenarios
Rarely confused with ES but occasionally proposed as an alternative by distributed systems practitioners


1.2  The Critical Distinction — EDA vs. Event Sourcing
This is the most important distinction to establish early, because the confusion between EDA and Event Sourcing causes the most significant architectural mistakes. If you have worked with Kafka, RabbitMQ, or any pub/sub system, you will arrive with EDA intuitions and attempt to apply them to event sourcing. These intuitions are wrong in specific, predictable ways.

DIMENSION
EVENT-DRIVEN ARCHITECTURE
EVENT SOURCING
Purpose of events
Notification: "something happened, whoever cares should react"
Persistence: "this is the authoritative record of what happened — the database IS the events"
What happens if an event is lost?
Downstream consumers miss a notification — this is often acceptable and handled by retry logic
The system's history is incomplete and state reconstruction is impossible — this is catastrophic
Event retention
Usually short-lived (hours to days); Kafka default retention is 7 days
Permanent by design; events from 5 years ago must be as readable as events from today
Consumer role
Consumers react to events and maintain their own state independently
The event stream IS the state; all state is derived from events
Schema evolution
Consumers can often tolerate schema changes with consumer-side adaptation
Historical events cannot be modified; all schema evolution happens at read time via upcasters
Ordering guarantee
Usually per-partition/per-topic ordering; global ordering is expensive
Strict ordering within a stream (by stream_position); global ordering via global_position
Concurrency model
Typically at-least-once delivery with consumer-side idempotency
Optimistic concurrency control — each write specifies expected version; conflicts are explicit
Typical tools
Kafka, RabbitMQ, Redis Streams, AWS EventBridge, NATS
EventStoreDB, Marten+PostgreSQL, Axon Framework, custom PostgreSQL schemas
Mutable state?
Consumers usually maintain mutable projections in separate databases
Projections are derived and rebuildable; the events are immutable; the projection IS mutable


In short, Event-Driven Architecture (EDA) focuses on the propagation of state changes, while Event Sourcing (ES) focuses on the definition of state.

The Mathematical Distinction

Event Sourcing (The Log is the Truth)
In ES, the state S at time t is a pure function of the history of events e from the beginning of time.
St = f( S0, [e1, e2, ..., et ] )


State: Is transient or a projection (cache). It can be deleted and perfectly recalculated by replaying the event log.
Storage: You store the operands (the events), not the result. 


EDA / Event-Driven (The Message is the Trigger). 
In a standard EDA system, events are used to notify other services. The state S is usually updated in place (CRUD) and the event is a side effect.
St = St-1 + Δ


State: Is the "Source of Truth." Once the database record is overwritten, the previous state is lost unless specifically archived.
Storage: You store the result, and the event is an ephemeral notification ($e_t$) sent over a wire. 

Key Comparisons

Feature
Event Sourcing (ES)
Event-Driven Architecture (EDA)
State Origin
Derived from the sum of all events.
Derived from the current record in a DB.
Auditability
Perfect (mathematically guaranteed).
Partial (depends on logging/tables).
Complexity
High (requires "folding" or snapshots).
Lower (standard pub/sub models).
Primary Goal
Data integrity and history.
Decoupling and scalability.


The Hybrid Reality: Most modern systems use both. You might use Event Sourcing inside a single microservice to keep a perfect history, and then emit those events via EDA to notify the rest of the ecosystem. Should we look into a specific code implementation or how snapshots are used to optimize ES performance?


The "What If" Test


When you find yourself confusing EDA and ES, use this diagnostic: "What happens if my message bus crashes and loses the last 100 events? In my current design, can I reconstruct the system's state?" If the answer is no, you have EDA, not event sourcing. The ability to reconstruct current state from first principles — by replaying from event 1 — is the definitional property of event sourcing. If the system cannot do this, it is not event-sourced.




1.3  CQRS — What It Is and Is Not
CQRS is the architectural pattern most frequently paired with event sourcing, but they are independent decisions. A system can use CQRS without event sourcing (separate read and write databases with synchronisation). A system can use event sourcing without CQRS (reading state by replaying the aggregate stream on every query — expensive at scale but valid for small systems). Most production event-sourced systems use both.
The CQRS Contract
SIDE
NAME
PRIMITIVE
CHARACTERISTICS
ES IMPLEMENTATION
Write
Command Side
Command → Domain Logic → Events
Strongly consistent; optimistic concurrency enforced; returns acknowledgement not data
append_events() to the event store; aggregate validates business rules before appending
Read
Query Side
Events → Projection → Read Model
Eventually consistent; optimised for query patterns; can have multiple read models from same events
Projections built by the async daemon; stored in Postgres tables optimised for the specific query


The most important property of CQRS in the event sourcing context: the write side never reads from the query side. Commands are validated against the aggregate's current state — which is reconstructed by replaying events — not against a projection. Projections can be stale; the aggregate event stream is always current. If a command handler reads from a projection to make a decision, the CQRS boundary has been violated.
Diagnostic Check: The Projection Read in Command Handler


Examine your credit analysis command handler. Where does it read the application's current state? If it points to a database table (a projection), you have violated the CQRS boundary. The command handler must reconstruct the LoanApplicationAggregate by replaying its event stream. This is slower than reading a projection but guarantees the command sees the authoritative state. The performance concern is real — it is solved by snapshotting, not by reading projections in commands.




1.4  DDD Integration — Aggregates, Bounded Contexts, Domain Events
Event sourcing is the natural persistence layer for DDD aggregates. The DDD aggregate is a consistency boundary — changes to the aggregate must be atomic and its invariants must always hold. An event is the DDD concept of a "domain event" made durable. The combination gives you: DDD for modelling (what are the right aggregates and events?), event sourcing for persistence (how do we store aggregate state?), and CQRS for access (how do we query efficiently?).
The DDD → Event Sourcing Mapping
DDD CONCEPT
EVENT SOURCING EQUIVALENT
IMPLEMENTATION NOTE
Aggregate
Event stream
One stream per aggregate instance: "loan-{id}", "agent-{id}-{session_id}"
Aggregate root
The entity identified by stream_id
stream_id encodes both aggregate type and identity
Domain event
Event stored in the stream
Events are named in past tense ("ApplicationSubmitted"), are immutable, and represent facts that occurred
Command
Input to the command handler
Commands are validated; they MAY produce events but they are not stored directly — only the resulting events are stored
Invariant
Business rule checked in aggregate.apply() before append
If the invariant is violated, append is rejected before writing to the store
Value object
Embedded in event payload
Value objects become JSON fields in the event payload; they are not aggregates and have no streams
Bounded context
Separate event stream namespace
Events in different bounded contexts use different stream_id prefixes; cross-context communication via published domain events, not shared streams
Anti-corruption layer
Event translator / upcaster at context boundary
Translates events from one bounded context's schema to another's; prevents schema leakage between contexts


The Ubiquitous Language Test


Read your event type names aloud to a non-technical stakeholder. If they understand what happened, the event names are correct domain language. If names like "UpdateUserStatus", "SetApplicationFlag", or "ModifyRecord" appear, you have mapped CRUD operations to events rather than modelling domain facts. CRUD events ("Updated", "Deleted", "Modified") are common early-stage mistakes. Real domain events: "ApplicationSubmitted", "CreditLimitExceeded", "FraudAlertRaised", "ComplianceRulePassed".





  PART II
The Deep Jargon Glossary
Every term a tutor needs to know with precision — including how trainees misuse them
This glossary is organised by conceptual cluster, not alphabetically. Terms that are regularly confused are grouped together so you can address the confusion directly. Each entry includes a note on the most common misunderstanding.

  CLUSTER A  ·  Core Storage Primitives  

Event Store
A database specialised for storing events in order. Not a general-purpose database with events bolted on. The event store guarantees: append-only writes (no update or delete), strict ordering within a stream via stream_position, global ordering across all streams via global_position, and ACID guarantees for appends. The two dominant implementations in 2026 are EventStoreDB (purpose-built) and PostgreSQL with a carefully designed events table (the approach used in The Ledger challenge).
In practice: 
‣  EventStoreDB: the purpose-built standard, with native gRPC streaming and persistent subscriptions
‣  PostgreSQL + Marten (.NET): enterprise-grade, single-database, production-proven
‣  PostgreSQL + psycopg3 (Python): what trainees build in the challenge — same patterns, no framework magic
Note


You might say "I'm using an event store" when using a message broker (Kafka) or a time-series database (InfluxDB). Test yourself: "Can I replay all events from position 0 to reconstruct current state, guaranteed, without data loss?" Kafka cannot guarantee this after retention expires. InfluxDB is not append-only-per-stream with optimistic concurrency. Neither is an event store.




Event Stream
The ordered sequence of events for a single aggregate instance. A stream is identified by a stream_id (e.g., "loan-a1b2c3") and contains all events that have ever been applied to that aggregate. Streams are the unit of optimistic concurrency — you cannot span a transaction across two streams without accepting that they may be at different versions at commit time. Streams are also the unit of archival — when an aggregate's lifecycle is complete, its stream can be archived (moved to cold storage) without affecting other streams.
In practice: 
‣  "loan-abc123" contains: ApplicationSubmitted, CreditAnalysisRequested, CreditAnalysisCompleted, DecisionGenerated, ApplicationApproved — the complete immutable history of that loan
‣  "agent-worker-1-session-42" contains the full action history of one AI agent's work session
Note


A common confusion: if you have used Kafka, you might think a "stream" is a topic with multiple producers. An event store stream is a single aggregate instance's history — it has one logical writer at a time (enforced by optimistic concurrency). The Kafka topic is the EDA concept; the event store stream is the ES concept.




Stream Position vs. Global Position
Stream position is the version number of an event within a single stream — starts at 1, increments by 1, unique per stream. Global position is a monotonically increasing sequence number across ALL events in the store — the order in which events were physically written. Both are needed: stream position for optimistic concurrency (expected_version=5 means "this stream should currently have 5 events"); global position for projection daemons (process all events from global_position=1000 onwards, regardless of which stream they belong to).
In practice: 
‣  Optimistic concurrency uses stream_position: "I read the loan stream and it was at version 3; I expect it to still be at version 3 when I append"
‣  Projection daemon uses global_position: "I last processed global position 8500; give me all events with global_position > 8500"
Note


If your projection daemon crashes and restarts, it must know where to resume. The answer is global_position stored in projection_checkpoints. If you replay from the beginning, you have not implemented checkpointing — your daemon is O(total_events) on every restart.




Aggregate
AG-reh-gate (noun) or ag-REH-gate (verb)  ·  DDD / Consistency Boundary
A consistency boundary — a cluster of domain objects that must be modified atomically and whose invariants must always hold. In event sourcing, an aggregate's state is the result of replaying all events in its stream. You cannot partially apply events — all events must be applied in order, or none. The aggregate is the unit of transactional consistency: you can guarantee consistency within one aggregate; you cannot guarantee it across two aggregates in a single operation without distributed transactions (which event sourcing deliberately avoids).
In practice: 
‣  LoanApplication is an aggregate: all state changes to a loan happen in the "loan-{id}" stream, atomically
‣  AgentSession is a separate aggregate: its events live in "agent-{id}-{session_id}" — a different consistency boundary
Note


The hardest aggregate design question: "How large should my aggregate be?" The temptation is a God Aggregate that contains everything. The problem: every write to ANY part of the aggregate contends for the same stream_position. 100 agents writing to one LoanApplication aggregate simultaneously = 99 OptimisticConcurrencyErrors per second. The correct response: make aggregates as small as the consistency requirement allows — which is usually smaller than you expect.




Optimistic Concurrency Control (OCC)
The mechanism that prevents two concurrent writers from creating an inconsistent event stream. Each write operation specifies the expected_version — the stream version the writer observed before making its decision. The event store checks: if current_version == expected_version, append succeeds and current_version increments. If current_version > expected_version (someone else appended since the writer read), raise OptimisticConcurrencyError. The writer must reload the stream, re-apply its business logic to the updated state, and retry if appropriate. No locks are held between read and write — hence "optimistic" (we optimistically assume no conflict; we verify atomically at write time).
In practice: 
‣  Agent A reads loan stream at version 3, computes credit decision. Agent B also reads loan stream at version 3, also computes fraud score. Both try to append at expected_version=3. One succeeds (version becomes 4). The other gets OptimisticConcurrencyError, reloads at version 4, and retries.
‣  For LoanApplication: on retry, the agent must check whether the analysis it was about to submit is still relevant given the new events — it may have been superseded
Note


When you first encounter OCC, you might ask: "Can't I just use a database lock?" Yes — but locking creates contention. If 100 agents are processing 100 different loans, OCC means each loan's stream has independent concurrency — no global lock bottleneck. With pessimistic locking, all 100 agents contend for a global lock. OCC is why event stores can handle high write throughput.




Snapshot
A periodic save of an aggregate's computed state that acts as a checkpoint during event replay. Without snapshots, loading an aggregate requires replaying every event from position 1. For a LoanApplication with 50 events, this is fast. For an aggregate with 50,000 events (a customer account with 10 years of transactions), this is unacceptably slow. A snapshot stores the aggregate's state at a specific stream_position. On load: find the most recent snapshot, load from that position, replay only the events since the snapshot. Snapshotting has hidden complexity: snapshot invalidation (if the aggregate's apply logic changes, old snapshots are invalid), snapshot versioning (snapshots must carry a schema version), and snapshot storage (where to keep them without bloating the events table).
In practice: 
‣  Snapshot trigger options: every N events (e.g., every 100), every T time (e.g., daily), on-demand (after specific event types)
‣  Snapshot storage options: same events table with a special event_type, separate snapshots table, Redis cache for hot aggregates
Note


The snapshot trap: you might implement snapshots and forget snapshot invalidation. If you change the aggregate's _apply() logic (e.g., add a new computed field), all existing snapshots are now wrong. You must either invalidate snapshots on deploy or carry a snapshot_schema_version field and reject snapshots that don't match the current schema.





  CLUSTER B  ·  Projections & Read Models  

Projection
A read-optimised view of data, built by processing events from the event store. A projection subscribes to one or more event types and maintains state (usually in a database table) as events are processed. Projections are eventually consistent with the event store — there is always a lag between an event being appended and the projection being updated. Projections are rebuildable: drop the projection table, replay all events from position 0, and the projection is reconstructed. This rebuildability is one of the most powerful properties of event sourcing — you can add a new projection at any time and backfill it with all historical data.
In practice: 
‣  ApplicationSummary projection: one row per loan application, updated as each event type is processed — the read model for the loan officer's dashboard
‣  AgentPerformanceLedger projection: aggregated statistics per model version — the read model for the AI ops team
Note


If your product team wants a new report: average time between ApplicationSubmitted and DecisionGenerated, by applicant industry sector. In a CRUD system, this might require a schema migration. In an event-sourced system, you create a new projection that subscribes to ApplicationSubmitted and DecisionGenerated events, backfill from position 0, and query the projection. No schema migration. No data loss. This "infinite flexibility" is real, but only if projections are designed correctly.




Inline Projection vs. Async Projection
Inline projections are updated synchronously in the same database transaction as the event write. Guaranteed consistent with the event store at all times. Higher write latency (the projection update is on the critical path). Async projections are updated by a background daemon after the event is written. Lower write latency (the write completes immediately; the projection catches up asynchronously). Eventually consistent — there is a lag window where the projection may not reflect the latest events. The choice depends on the read model's consistency requirements: if a UI must immediately reflect a write, use inline; if it can tolerate a few hundred milliseconds of lag, use async.
In practice: 
‣  ApplicationSummary: could be inline (immediate consistency for the loan officer dashboard) or async with <500ms SLO
‣  AgentPerformanceLedger: always async — stale-by-seconds is acceptable for an analytics dashboard
Note


The consistency trap: you might default to inline projections because they're simpler. But inline projections mean every write pays the cost of updating every projection. As projections multiply, write latency grows proportionally. Production systems almost always move critical read models to async with tight SLOs.




Projection Checkpoint / Daemon Checkpoint
The last global_position that a projection daemon has successfully processed. Stored in a projection_checkpoints table. When the daemon restarts (crash, deploy, scale), it reads its checkpoint and resumes from that position — not from 0. Without checkpointing, every restart causes a full replay which is O(total_events) and gets slower as the system matures. Checkpointing is what makes the async daemon production-safe. The checkpoint must be updated atomically with the projection update — if the projection table is updated but the checkpoint is not, the daemon will reprocess events and the projection must be idempotent (handling the same event twice must produce the same result as handling it once).
In practice: 
‣  After processing events 1–8500, checkpoint = 8500; on restart, daemon queries "SELECT * FROM events WHERE global_position > 8500"
‣  Idempotency requirement: if ProcessedApplicationSubmitted is called twice with the same application_id, the second call must not create a duplicate row
Note


The idempotency test: deliberately process the same batch of events twice through a projection and assert the state is identical to processing it once. Every projection must pass this test to avoid corrupting state after a daemon restart.




Projection Rebuild / Replay
The process of discarding a projection's current state and rebuilding it by replaying all events from position 0. This is how you add new projections to a system with historical data, fix projection bugs, and recover from corruption. Rebuilding must happen without downtime to live reads — the old projection must remain queryable while the new version is being built, then swapped atomically. The Blue/Green projection pattern: build the new projection in a "green" table while the "blue" table serves live traffic; swap at completion.
In practice: 
‣  Adding a new projection to a 3-year-old system: create the table, set checkpoint to 0, start daemon — it replays 3 years of events to backfill
‣  Fixing a projection bug: rename current table to _backup, create new table, replay from 0, verify, drop _backup
Note


How long does a full rebuild take on your system? You should know this number to understand your system's operational characteristics. A rebuild that takes 10 minutes is acceptable; 10 hours is not — you need to fix either event volume or build efficiency before going to production.





  CLUSTER C  ·  Schema Evolution & Migration  

Upcaster
A function that transforms an event of an old schema version into an event of a newer schema version, applied at read time without modifying the stored event. Upcasters are the event sourcing solution to schema evolution. The stored event is immutable — you can never change what was written. The upcaster transforms the payload in memory as events are loaded, so the rest of the system always sees the current schema. Upcasters are chained: if an event evolves from v1 to v3, the chain v1→v2→v2→v3 is applied automatically. Every upcaster must be deterministic (same input, same output), must not call external services, and must never write to the database.
In practice: 
‣  v1 CreditAnalysisCompleted: {application_id, risk_tier, recommended_limit_usd}
‣  v2 CreditAnalysisCompleted: adds {model_version, confidence_score}
‣  Upcaster v1→v2: infer model_version from recorded_at timestamp; set confidence_score=null (genuinely unknown — fabrication is worse than null)
Note


The null vs. fabrication decision is a hard judgment call. When a new required field is added, you must provide a value for historical events. Rule: never fabricate a value that will be treated as accurate data. If a compliance system reads it, a fabricated value is worse than null — it will cause incorrect regulatory decisions.




Event Schema Versioning
The practice of tagging each stored event with the schema version it was created under (event_version field in the events table). This enables the upcaster registry to know which transformation chain to apply when loading an event. Without version tracking, upcasters must infer the version from payload content — fragile and error-prone. Schema versioning should be established from day one even if no upcasters exist yet: it costs nothing to store, and retrofitting version tracking onto a production system with millions of unversioned events is extremely painful.
In practice: 
‣  event_version=1: original schema; no upcaster needed
‣  event_version=2: added regulatory_basis field; upcaster v1→v2 infers it from rule versions active at recorded_at
‣  event_version=3: renamed risk_tier to risk_level; upcaster v2→v3 renames the field
Note


What is the current event_version of your CreditAnalysisCompleted events? If you cannot answer immediately, version tracking is not implemented correctly. It should be a constant on the event class.




Backward Compatibility vs. Breaking Change (in event schemas)
Backward-compatible changes allow existing consumers to process new events without modification: adding new optional fields, adding new event types. Breaking changes require upcasters or consumer updates: renaming fields, removing fields, changing field types, changing the semantics of a field (e.g., changing a field from representing cents to dollars). The key test for backward compatibility: can every existing upcaster and projection still function correctly if it receives the new event schema without modification? If yes, the change is backward-compatible.
In practice: 
‣  Backward-compatible: add optional field "branch_code" to ApplicationSubmitted — existing projections ignore it
‣  Breaking: rename "amount_cents" to "amount_usd" — existing projections reading "amount_cents" get null, causing silent data corruption
Note


The silent corruption problem is the worst failure mode. Always ask: "What happens to every existing projection if I make this change?" The answer should be explicit, not assumed.




Aggregate Root Versioning vs. Event Versioning
Two different things called "version" in event sourcing. Aggregate version (also called stream_position) is the number of events in the stream — used for optimistic concurrency control. Event schema version (event_version) is the version of the event's payload schema — used for upcasting. These are completely independent: a stream at aggregate version 47 might contain events with event_version 1 (old schema) and events with event_version 2 (new schema) mixed together. The aggregate version tracks "how many events have happened"; the event version tracks "what schema was used when this event was created".
In practice: 
‣  stream_position=47 means this aggregate has had 47 events applied to it — used in expected_version check
‣  event_version=2 on a particular event means its payload must be processed through the v1→v2 upcaster chain
Note


This distinction causes persistent confusion because both are called "version." Clarify: are you looking at the aggregate stream version for concurrency or the event schema version for upcasting? They are different columns with completely different semantics.





  CLUSTER D  ·  Enterprise & Distributed Patterns  

Outbox Pattern
The solution to the dual-write problem: writing to the event store and publishing to an external message bus (Kafka, Redis Streams) atomically. Without the outbox, these two writes happen in separate transactions — if the event store write succeeds but the Kafka publish fails, your projections and external systems are inconsistent. The outbox table lives in the same database as the event store. On event append: write the event to the events table AND write a corresponding row to the outbox table, in the same database transaction. A separate poller reads the outbox and publishes to Kafka, marking rows as published. Transactional Outbox Pattern is the formal name; "outbox" is the universal term.
In practice: 
‣  Events table write + outbox table write = one PostgreSQL transaction — either both succeed or both fail
‣  Outbox poller reads unacknowledged outbox rows, publishes to Kafka, marks published_at — idempotent, retryable
Note


The outbox pattern works with any database + any message bus combination. It is the implementation-agnostic solution for enterprise integration.




Saga / Process Manager
A stateful process that coordinates multi-step business workflows by reacting to events and issuing commands. In event-sourced systems, a saga listens to domain events and, based on its current state, decides whether to issue the next command in a workflow. Sagas have their own event stream (or state store) to track their current position in the workflow. The saga pattern comes in two flavours: Choreography (each service reacts to events and emits its own without central coordination) and Orchestration (a dedicated saga coordinator explicitly issues commands to each participant service). Both are implemented on top of the event store.
In practice: 
‣  Loan approval saga: on CreditAnalysisCompleted → issue RequestFraudScreening command; on FraudScreeningCompleted → issue RequestComplianceCheck; on all checks complete → issue GenerateDecision command
‣  Timeout handling: if FraudScreeningCompleted is not received within 30 seconds, the saga issues an EscalateToHuman command
Note


Don't conflate the saga with the aggregate. The aggregate enforces business rules for a single entity; the saga orchestrates workflows across multiple aggregates. They are different things and should never be merged.




Eventual Consistency vs. Strong Consistency
In CQRS systems with async projections, the write side (event store) and read side (projections) are eventually consistent — there is a window of time where a read might return stale data. The duration of this window is the projection lag. Strong consistency means reads always reflect the latest write. In event-sourced systems: aggregate state reconstruction via event replay is strongly consistent (you see every event); projection reads are eventually consistent (you see the projection as of the last daemon checkpoint). The consistency requirement for a feature determines which to use for that feature's read operations.
In practice: 
‣  User just approved a loan — they expect to immediately see "Approved" on the dashboard: either use inline projection (strongly consistent) or implement read-after-write consistency at the application layer
‣  Analytics dashboard showing approval rates by risk tier: eventual consistency with 5-second lag is acceptable
Note


The UI timing problem: a user takes an action and immediately navigates to a screen that reads from a projection. If the projection has not caught up, they see stale data. The solution is read-after-write consistency, which must be explicitly designed.




Idempotency (in event processing)
An operation is idempotent if performing it multiple times produces the same result as performing it once. In event sourcing, projection handlers must be idempotent because at-least-once delivery guarantees may cause an event to be delivered to a projection more than once (after daemon restart, after network failure, during replay). A non-idempotent projection will accumulate duplicate state. Idempotency strategies: primary key on the event_id in the projection table (duplicate inserts fail gracefully), tracking processed event IDs in a processed_events table, using UPSERT (insert or update) semantics instead of INSERT.
In practice: 
‣  Non-idempotent: INSERT INTO application_summary VALUES (...) — second call creates duplicate row
‣  Idempotent: INSERT INTO application_summary VALUES (...) ON CONFLICT (application_id) DO UPDATE SET ... — second call updates existing row to same state
Note


The idempotency test should be part of every projection's test suite. This is a production safety requirement, not just good practice.





  CLUSTER E  ·  AI-Era Extensions  

Agent Memory via Event Replay (Gas Town Pattern)
The pattern of using an agent's event stream as its durable memory, enabling full context reconstruction after a crash or restart. An AI agent appends an AgentContextLoaded event at session start (recording what data it accessed and its model version), then appends an event for every significant action it takes. If the agent crashes, it can be restarted, its event stream replayed, and a context summary reconstructed from the event history — enabling it to continue without repeating work or losing decisions made before the crash. Named "Gas Town" because it solves the "ephemeral memory" problem of command-line agents described in the Tenacious infrastructure work.
In practice: 
‣  Agent starts: appends AgentContextLoaded with {model_version, context_source, token_count}
‣  Agent makes decision: appends CreditAnalysisCompleted with {decision, confidence, input_data_hash}
‣  Agent crashes; is restarted: calls reconstruct_agent_context() which replays the session stream and produces a context summary for the LLM
Note


The key insight: the event store IS the agent's memory. Reconstructing summaries from the event store enables agents to work on tasks spanning hours without context window exhaustion.




Causal Chain (correlation_id + causation_id)
The mechanism for tracing why an event occurred — not just what occurred. Every event carries two metadata fields: correlation_id (the ID of the original request or workflow that initiated the entire causal chain — stays the same across all events in the same business transaction) and causation_id (the ID of the specific event that directly caused this event to be created). Together, they form a graph: following causation_ids from any event backwards traces the complete causal history of that decision. This is mandatory for regulatory compliance ("what data and model caused this credit decision?") and essential for debugging ("which recommendation caused this schedule adjustment?").
In practice: 
‣  Request comes in with correlation_id=C42. ApplicationSubmitted has correlation_id=C42, causation_id=null (it is the root). CreditAnalysisRequested has correlation_id=C42, causation_id=event_id of ApplicationSubmitted. CreditAnalysisCompleted has correlation_id=C42, causation_id=event_id of CreditAnalysisRequested.
‣  Full causal chain: ApplicationSubmitted → CreditAnalysisRequested → CreditAnalysisCompleted → DecisionGenerated → ApplicationApproved
Note


The counterfactual test: can you trace ApplicationApproved back to the exact model version and input data hash? If any link is missing or causation_ids are null, your audit trail is incomplete and the system will fail regulatory examination.




Counterfactual Projection / What-If Analysis
A read-only operation that replays a portion of the event stream with one or more events substituted (the "counterfactual") and evaluates what the system state would have been under that alternative history. Used for: regulatory examination ("what would the decision have been with last month's model?"), model improvement analysis ("how many decisions would have changed if we had used the v3 risk model?"), and debugging ("was the agent's decision wrong because of bad input data or bad model logic?"). Counterfactual events exist only in memory during the projection run — they are NEVER written to the event store.
In practice: 
‣  Counterfactual: substitute CreditAnalysisCompleted with risk_tier=HIGH instead of MEDIUM; re-run the decision projection; check if the final decision changes
‣  Causal dependency filtering: events that are causally dependent on the substituted event must be replaced by counterfactual consequences; events that are causally independent (e.g., a parallel fraud screening) are replayed unchanged
Note


Causal dependency filtering is critical. If you substitute an event, you must also substitute or skip all downstream events that trace back to it, otherwise the counterfactual is contaminated.






  PART III
The KSBC Framework
Knowledge, Skills, Behaviours & Competencies — what mastery looks like at each level
The KSBC framework maps four dimensions of expertise. Knowledge is what you know. Skills are what you can do. Behaviours are your thought patterns and habits. Competencies are demonstrations of all three under real conditions. Use this as a self-assessment tool as you prepare for enterprise roles.

How to Use This Framework


Use this as a diagnostic lens for your own development. Identify which domain is your current bottleneck. If you know patterns but cannot implement them, you have a Skill gap. If you can implement but cannot explain tradeoffs, you have a Behaviour gap. Focus your learning on the areas where you need the most growth.




  KNOWLEDGE — What You Must Know Before You Can Reason Correctly  

KNOWLEDGE DOMAIN
Observable Indicators — What is present when you master this


Core ES Primitives
Events, streams, global position, append-only semantics
You can define an event store and distinguish it from a CRUD database without prompting
You can explain stream_position vs. global_position without confusion
You can articulate why the past is immutable and what that means for schema evolution
You know the ACID guarantees required of an event store and why they matter
Pattern Relationships
ES, EDA, CQRS, DDD, Saga — distinct and related
You can map the relationships between ES, EDA, CQRS, DDD without mixing them
You can give an example of each pattern used without the others
You can explain why CQRS does not require ES and ES does not require CQRS
You can identify when a Saga is appropriate vs. when aggregate design should be changed
Concurrency & Consistency
OCC, eventual consistency, consistency boundaries
You can explain optimistic concurrency control with a concrete example
You can articulate the consistency model of async projections (eventual consistency)
You can identify the consistency requirement for a given business feature and choose the appropriate read model
You know the difference between aggregate-level consistency and cross-aggregate coordination
Schema Evolution
Upcasting, versioning, backward compatibility
You can classify schema changes as backward-compatible or breaking
You can write an upcaster for a realistic schema change
You understand null vs. inferred vs. default value tradeoffs for missing historical fields
You can explain why snapshot invalidation is required after aggregate apply() logic changes
Enterprise Stack
EventStoreDB, Marten, PostgreSQL, Kafka integration
You can map EventStoreDB concepts to PostgreSQL equivalents
You understand the Marten Async Daemon pattern and can implement its equivalent in Python
You know when to use the Outbox Pattern and can implement it
You can explain the difference between Kafka as event bus vs. PostgreSQL as event store
AI-Era Patterns
Agent memory, causal chains, counterfactual projections
You can explain the Gas Town persistent memory pattern and implement AgentContextLoaded
You understand correlation_id + causation_id and can trace a complete causal chain
You know the counterfactual projection concept and its causal dependency constraint
You can explain how event sourcing enables regulatory auditability for AI decisions


  SKILLS — What You Must Be Able to Do Under Timed Conditions  

SKILL AREA
Observable Indicators — What is present when you master this


Event Store Implementation
Build a production-quality append-only store
You implement the events table schema correctly (all required columns, indexes, constraints)
You implement append_events() with optimistic concurrency in a single database transaction
You implement load_stream() with upcaster application transparently
You implement load_all() as an async generator with configurable batch sizes
You pass the double-decision test (concurrent append conflict handling
Aggregate Design & Domain Logic
Model business rules as aggregates
You identify correct aggregate boundaries for a given business domain
You implement the load() → apply events → validate → append pattern correctly
You enforce all business invariants in domain logic
You implement state machine transitions and rejects invalid state changes
You name events in past-tense domain language
Projection Building
Build efficient, rebuildable read models
You implement a projection handler with correct idempotency
You implement the ProjectionDaemon with checkpoint management
You expose projection lag as a measurable metric
You can rebuild a projection from scratch without downtime to live reads
You meet stated SLOs under simulated load
Upcaster Implementation
Handle schema evolution without store mutation
You implement UpcasterRegistry with automatic chain application
You write a realistic upcaster with justified inference strategy
You pass the immutability test (store is never written during upcasting)
You implement upcaster tests
You understand and can articulate null vs. fabrication tradeoffs
MCP Tool & Resource Design
Design event store interfaces for AI agent consumption
You design Tools (Commands) and Resources (Queries) as structural CQRS implementation
You implement structured error types that LLM consumers can reason about
You document preconditions in tool descriptions
You ensure Resources read only from projections
You pass full lifecycle integration tests using only MCP tool calls


  BEHAVIOURS — Thought Patterns That Emerge From Experience  

Behaviours are the hardest dimension to teach because they are not transferable through instruction — they emerge from experience navigating real systems and real failures. The tutor's role is to create the conditions under which these behaviours develop, not to explain them. The following table describes what to look for and how to create opportunities for each behaviour to emerge.

BEHAVIOUR
Observable Indicators — What is present when you master this


Fact-Not-State Thinking
Instinctively models the world as facts that happened rather than state that exists
You spontaneously describe business requirements using past-tense domain events
When confronted with a new requirement, you ask "what are the facts I need to record?" before "what fields do I need to store?"
You catch yourself naming events with CRUD verbs and self-correct to domain language
You can walk through a business scenario and generate a complete event catalogue independently
Consistency Boundary Instinct
Automatically identifies where consistency requirements begin and end
When designing aggregates, your first question is "what is the smallest consistent unit?"
You recognise aggregate-size bloat and articulate the concurrency cost
When given a multi-aggregate business operation, you design a saga rather than cross-aggregate transactions
You can immediately identify which aggregate owns a given business rule when a new requirement arrives
Schema Immortality Awareness
Treats the event store as containing data that will outlive the current codebase
Before adding any field to an event, you ask "what will the upcaster look like when this field must change?"
You add event_version to every event schema from day one
You never fabricate historical field values in upcasters without documentation
You ask "what happens to events written 3 years from now that use this schema?"
Causal Tracing Reflex
Automatically thinks in terms of why things happened, not just what happened
Every event has correlation_id and causation_id populated
When debugging, your first question is "what is the causal chain that led to this state?"
You design agent actions so every automated decision references the data and model version used
You can answer "who authorised this action and what made them authorise it?" for any event
Lag Consciousness
Treats projection lag as a system property that must be designed for, not an acceptable background condition
You report projection lag in milliseconds, not "fast" or "low"
You define projection SLOs before implementing projections
When designing a new feature, your first question about reads is "what is the acceptable consistency window?"
You design read-after-write consistency at the application layer when needed
Immutability as a Design Constraint
Designs new features assuming the event log already exists and cannot be modified
When asked to "just update old events," you explain why this violates the fundamental guarantee and propose an upcaster
You treat the event catalogue as a contract with the future
When a bug is found in historical data, your first response is "design a compensating event" not "run an UPDATE"
You understand that append-only is a feature, and can explain why to a stakeholder
Projection Rebuild Orientation
Treats every projection as a temporary view that might need to be rebuilt
You design projections with rebuild in mind from the start
When a new reporting requirement arrives, your first question is "can I build a new projection from existing events?"
When optimising a slow query, you consider rebuilding the projection before adding indexes
You know and monitor projection rebuild time as a system health metric


  COMPETENCIES — Integrated Performance Under Real Conditions  

Competencies are demonstrated by navigating ambiguous, realistic scenarios — not by passing checklist tests. The following competency definitions describe what a trainee must be able to do to be ready for an enterprise event sourcing role. Each competency has a Level 1 (trainee), Level 2 (practitioner), and Level 3 (principal) descriptor.

COMPETENCY
LEVEL 1 — Trainee
LEVEL 2 — Practitioner
LEVEL 3 — Principal Practitioner


Event Catalogue Design
Can generate events for a domain with guidance; uses some CRUD verbs; misses edge cases


Generates complete event catalogue independently; all domain language; identifies edge cases


Designs event catalogues that are immediately readable by domain experts; identifies missing events that requirements didn't specify; anticipates schema evolution needs
Aggregate Boundary Decisions
Implements aggregates that work but are too large or arbitrarily bounded


Correctly sizes aggregates to consistency requirements; can justify boundary choices


Identifies aggregate boundary traps in existing systems; redesigns boundaries under live concurrency pressure; can explain the coupling cost of any boundary choice in business terms
Production Incident Response
Needs guidance to replay events for debugging


Uses event replay as the first debugging tool; reconstructs state from history


Leads regulatory examinations using event streams; writes counterfactual projections to isolate root causes; produces tamper-evident audit packages on demand
Schema Migration Planning
Can write a upcaster with guidance; does not plan ahead for evolution


Writes upcasters independently; plans evolution paths before implementing changes


Reviews schema changes for long-term upcasting implications; maintains a schema evolution roadmap; makes null-vs-fabrication decisions with documented rationale
Performance Under Load
Implements working system; has not considered high-volume characteristics


Has modelled throughput; knows aggregate hot spots; has tested OCC retry rates


Can predict OCC collision rates from business logic analysis; optimises write throughput via QuickAppend modes and stream partitioning; designs snapshot strategies from first principles
Client Communication
Can explain event sourcing technically to engineers


Can explain business value (auditability, flexibility) to non-technical stakeholders


Can conduct the "should we use event sourcing?" conversation with an enterprise client; communicates one-way door decision correctly





  PART IV
The Event Schema Design Reference
Canonical schemas, field-level rationale, and design decision patterns for production event stores
This reference section provides production-ready schema definitions with the rationale for every design decision. The tutor should use these as the canonical answer when trainees question why a particular column exists or a constraint is defined a certain way. Each decision in these schemas was made because its absence caused a production failure somewhere in the industry.

  4.1  Core Event Store Tables  

  events (Primary table — the source of truth)
Every state change in the system is stored here. This is the only table that grows forever and can never be updated or deleted.

event_id  UUID PK DEFAULT gen_random_uuid()   — Globally unique identifier. Always UUID — never integer sequences (which leak event volume and are hard to shard). gen_random_uuid() is Postgres 14+ native; use uuid-ossp extension on older versions.
stream_id  TEXT NOT NULL   — Encodes both aggregate type and instance: "loan-{uuid}", "agent-{id}-{session}". Text not UUID: stream IDs must be human-readable for debugging and operational queries. Use consistent naming convention enforced by application layer.
stream_position  BIGINT NOT NULL   — Position of this event within its stream. Starts at 1. Combined with stream_id forms the unique constraint for optimistic concurrency. BIGINT not INT — systems running for years can exceed INT range on active streams.
global_position  BIGINT GENERATED ALWAYS AS IDENTITY   — Monotonically increasing across ALL events. Used by projection daemons to resume from checkpoint. GENERATED ALWAYS prevents application from setting it manually — this is intentional: the database owns global ordering.
event_type  TEXT NOT NULL   — String name of the event: "CreditAnalysisCompleted". Use consistent naming: PascalCase, past tense, no abbreviations. This is the routing key for upcasters and projections.
event_version  SMALLINT NOT NULL DEFAULT 1   — Schema version of this event's payload. Starts at 1. Increment when payload schema changes. SMALLINT (2 bytes) is sufficient — event schemas rarely exceed version 10 in practice.
payload  JSONB NOT NULL   — The event's data. JSONB (binary JSON) not JSON: JSONB indexes are efficient, JSONB queries are fast, JSONB validates structure. Never store PII here without encryption — this table is permanent and auditable.
metadata  JSONB NOT NULL DEFAULT '{}'   — Cross-cutting context: correlation_id, causation_id, agent_id, model_version, user_id, ip_address, trace_id. Kept separate from payload to avoid polluting domain event schemas with infrastructure concerns.
recorded_at  TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()   — When the event was recorded. clock_timestamp() not NOW() — NOW() returns the transaction start time; clock_timestamp() returns the actual write time. For events within one transaction, NOW() gives them identical timestamps which is misleading.
Key Indices:
UNIQUE (stream_id, stream_position) — the concurrency control constraint
INDEX (stream_id, stream_position) — range scan for load_stream()
INDEX (global_position) — range scan for projection daemon
INDEX (event_type) — filter queries by event type
INDEX (recorded_at) — time-range queries for audit and compliance
BRIN INDEX (recorded_at) — efficient for append-only time-ordered data; much smaller than B-tree
Design Note
The UNIQUE constraint on (stream_id, stream_position) is what makes optimistic concurrency work. The database enforces it atomically — two concurrent inserts with the same (stream_id, stream_position) cannot both succeed. One gets a unique constraint violation, which the application translates to OptimisticConcurrencyError. This is the only lock-free concurrency mechanism needed.


  event_streams (Stream metadata registry)
Tracks the current version and metadata of each aggregate stream. Updated atomically with every event append.

stream_id  TEXT PRIMARY KEY   — Matches events.stream_id. The canonical identifier for this aggregate instance.
aggregate_type  TEXT NOT NULL   — The type component of stream_id: "loan", "agent", "compliance". Enables queries like "all active loan streams".
current_version  BIGINT NOT NULL DEFAULT 0   — The current stream_position of the most recent event. Updated on every append. Used for optimistic concurrency check without a COUNT() query on the events table.
created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()   — When the stream was first created (first event appended).
archived_at  TIMESTAMPTZ (nullable)   — Set when the stream is archived. Archived streams are logically closed — no new events can be appended. Queries filter on archived_at IS NULL for active streams.
metadata  JSONB NOT NULL DEFAULT '{}'   — Stream-level metadata: tags, owning team, data classification (PII, financial, regulated). Used for operational management and compliance queries.
Key Indices:
INDEX (aggregate_type, archived_at) — list active streams by type
Design Note
current_version in event_streams enables the optimistic concurrency check to be O(1): "SELECT current_version FROM event_streams WHERE stream_id = $1" is a primary key lookup. Without this table, the check requires "SELECT MAX(stream_position) FROM events WHERE stream_id = $1" which becomes slower as the stream grows. This is the performance optimisation that makes high-throughput append viable.


  projection_checkpoints (Daemon state tracking)
Tracks the last successfully processed global_position for each projection. The daemon reads this on startup to resume without full replay.

projection_name  TEXT PRIMARY KEY   — Unique identifier for this projection: "application_summary", "agent_performance_ledger"
last_position  BIGINT NOT NULL DEFAULT 0   — The global_position of the last event successfully processed. On restart, daemon queries events WHERE global_position > last_position.
updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()   — When the checkpoint was last updated. Used for lag monitoring: NOW() - updated_at gives the approximate lag for a daemon that has not processed any events recently.
Key Indices:
PRIMARY KEY (projection_name) — single row per projection, fast upsert
Design Note
The checkpoint must be updated in the same transaction as the projection table update — not before, not after. If the projection is updated but the checkpoint is not, the daemon will reprocess events on restart (requiring idempotent handlers). If the checkpoint is updated but the projection is not (due to a crash), the daemon will skip events — which is catastrophic. Always: UPDATE projection tables AND UPDATE projection_checkpoints in a single database transaction.


  outbox (Reliable event publishing)
Events to be published to external systems. Written in the same transaction as the events table. Polled by the outbox publisher for delivery to Kafka, Redis Streams, or other buses.

id  UUID PRIMARY KEY DEFAULT gen_random_uuid()   — Independent ID from event_id — one event may generate multiple outbox entries (e.g., publish to Kafka AND send a webhook).
event_id  UUID NOT NULL REFERENCES events(event_id)   — Foreign key to the source event. Enables the publisher to retrieve full event context if needed.
destination  TEXT NOT NULL   — The target: "kafka:loan-events", "redis:agent-actions", "webhook:compliance-api". Allows the publisher to route to the correct bus.
payload  JSONB NOT NULL   — The message payload to publish. May differ from the event payload (e.g., stripped of internal fields, transformed to the external event schema).
created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()   — When the outbox entry was created.
published_at  TIMESTAMPTZ (nullable)   — NULL = not yet published. Set by the publisher on successful delivery. The publisher polls WHERE published_at IS NULL.
attempts  SMALLINT NOT NULL DEFAULT 0   — Delivery attempt count. Used to implement backoff and dead-lettering (if attempts > max_retries, move to dead letter).
Key Indices:
INDEX (published_at, created_at) WHERE published_at IS NULL — efficient poll for unpublished entries
Design Note
The outbox publisher must be idempotent at the destination. If the publisher delivers a message to Kafka and then crashes before marking published_at, it will redeliver on restart. The Kafka consumer (projection or external system) must handle duplicate messages gracefully. This is the at-least-once delivery guarantee. Exactly-once requires distributed transaction support (Kafka transactions) which adds significant complexity — at-least-once with idempotent consumers is the standard enterprise pattern.


  snapshots (Performance optimisation for high-volume streams)
Periodic saves of aggregate state to avoid full-stream replay. Use only when load_stream() latency exceeds acceptable thresholds — typically when streams exceed ~500 events for latency-sensitive operations.

snapshot_id  UUID PRIMARY KEY DEFAULT gen_random_uuid()   — Unique identifier for this snapshot.
stream_id  TEXT NOT NULL REFERENCES event_streams(stream_id)   — The stream this snapshot is for.
stream_position  BIGINT NOT NULL   — The stream_position of the most recent event included in this snapshot.
aggregate_type  TEXT NOT NULL   — Used to select the correct deserialiser when loading the snapshot.
snapshot_version  INT NOT NULL   — Schema version of the snapshot data — different from event_version. Must be validated against current aggregate apply() logic version on load.
state  JSONB NOT NULL   — The serialised aggregate state at stream_position. Must be the complete state needed to continue applying events from stream_position+1.
created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()   — When the snapshot was taken.
Key Indices:
INDEX (stream_id, stream_position DESC) — find most recent snapshot for a stream
Design Note
snapshot_version is the field most often forgotten in snapshot implementations. When aggregate apply() logic changes (e.g., a new computed field is added), snapshots taken with the old logic are invalid — they will produce incorrect state if loaded. On load, check: if snapshot.snapshot_version != CURRENT_AGGREGATE_SNAPSHOT_VERSION, discard the snapshot and fall back to full replay. The performance cost of an occasional full replay is much lower than the correctness cost of loading a stale snapshot.



  4.2  Event Payload Schema Patterns  

Event payload schemas are the contracts between the present and the future. Well-designed payloads are: minimal (only the facts that happened, no derived or computed values), self-contained (no foreign keys that require cross-aggregate lookups to understand), and evolution-friendly (designed with the first upcaster already in mind).

Pattern 1 — Identity Events (stream initiation)
Every stream starts with an identity event that records the aggregate's initial facts. The identity event must contain enough information to understand the aggregate's context without loading any other stream.
Identity event — correct vs. incorrect
# CORRECT: Self-contained identity event
class ApplicationSubmitted(BaseEvent):
    event_type: str = "ApplicationSubmitted"
    event_version: int = 1
    # Identity fields
    application_id: UUID
    applicant_id: UUID
    applicant_name: str            # Denormalised from applicant record
    # Business facts
    requested_amount_usd: Decimal
    loan_purpose: LoanPurpose      # Enum, not string — enforced vocabulary
    submission_channel: str        # "web" | "mobile" | "agent" | "branch"
    submitted_at: datetime

# WRONG: Thin identity event requiring cross-aggregate lookup
class ApplicationSubmitted(BaseEvent):
    application_id: UUID           # All other data requires separate query
    applicant_id: UUID             # Who is this? Cannot tell without loading applicant stream

The Denormalisation Rule
Event payloads should denormalise data that will be needed to understand the event in isolation. A future auditor or regulator looking at an event in isolation must be able to understand it without loading related aggregates. This means: include the applicant's name in ApplicationSubmitted even though it's also in the applicant record; include the session's context summary in AgentContextLoaded even though it's also in the context database. The cost is storage (cheap); the benefit is auditability (invaluable).


Pattern 2 — Decision Events with Causal Chain
Events that record a decision must carry the full causal chain — not just what was decided, but the data and model version that informed the decision. This is the event sourcing implementation of the AI governance requirement.
Decision event with full provenance chain
class CreditAnalysisCompleted(BaseEvent):
    event_type: str = "CreditAnalysisCompleted"
    event_version: int = 2
    # What was decided
    application_id: UUID
    risk_tier: RiskTier            # HIGH | MEDIUM | LOW
    recommended_limit_usd: Decimal
    confidence_score: float        # 0.0 - 1.0
    # How it was decided (causal provenance)
    agent_id: str
    session_id: UUID
    model_version: str             # "credit-model-v2.4.1"
    model_deployment_id: UUID      # Specific deployment, not just version
    input_data_hash: str           # SHA-256 of all input data — not the data itself
    analysis_duration_ms: int
    # Regulatory context
    regulatory_basis: list[str]    # List of regulation IDs this analysis satisfies

# metadata (set by EventStore, not by the domain event):
# {
#   "correlation_id": "...",       # Original request ID
#   "causation_id": "...",         # event_id of CreditAnalysisRequested
#   "agent_id": "credit-worker-3", # Who appended this event
# }


Pattern 3 — Compensating Events (not corrections, not deletions)
When something goes wrong — a wrong amount was entered, a rule was misapplied, a fraud score was recalculated — the correct response is a compensating event, not a modification of the original. Compensating events preserve the history of what went wrong and create an audit trail of the correction.
Compensating event pattern
# A CreditAnalysisCompleted was submitted with an incorrect risk tier
# WRONG: update the stored event (breaks immutability)
# UPDATE events SET payload = ... WHERE event_id = ... -- NEVER DO THIS

# CORRECT: append a compensating event
class CreditAnalysisCorrected(BaseEvent):
    event_type: str = "CreditAnalysisCorrected"
    event_version: int = 1
    application_id: UUID
    original_event_id: UUID        # References the incorrect CreditAnalysisCompleted
    corrected_risk_tier: RiskTier
    corrected_limit_usd: Decimal
    correction_reason: str         # Required — must explain why
    corrected_by: str              # Who authorised the correction
    corrected_at: datetime

# The aggregate's apply() handles CreditAnalysisCorrected by overwriting
# the risk_tier and limit in the reconstructed state — but the original
# CreditAnalysisCompleted remains in the stream, permanently, as evidence
# of what happened and when the correction was made.

The Correction Audit Requirement
In regulated industries, corrections are themselves regulated events. A loan risk assessment that was corrected after the fact must show: the original assessment, the correction, who authorised it, and why. An event store that allows modification of stored events cannot satisfy this requirement. An event store that uses compensating events satisfies it automatically — the complete correction history is in the stream.


  4.3  Event Naming Convention Reference  

NAMING RULE
CORRECT EXAMPLES
INCORRECT EXAMPLES
WHY IT MATTERS
Past tense — facts that occurred
ApplicationSubmitted, CreditAnalysisCompleted, ComplianceRulePassed
SubmitApplication, CompleteCreditAnalysis, PassComplianceRule
Commands are present tense (intentions); events are past tense (facts). Mixing them causes confusion about whether a concept is an input or an output
Domain language — no CRUD verbs
SessionBooked, FraudAlertRaised, ApplicationWithdrawn
UserCreated, RecordUpdated, StatusChanged, DataModified
CRUD verbs describe database operations, not business facts. "ApplicationWithdrawn" tells you something happened in the business domain; "RecordUpdated" tells you a row changed
Specific — not generic
SeatReserved, LimitExceeded, AgentContextLoaded
EventCreated, StatusUpdated, ProcessCompleted
Generic names force readers to examine the payload to understand what happened. Specific names communicate intent immediately
Noun + past participle
OrderShipped, InvoicePaid, PolicyRenewed
ShippedOrder, PaidInvoice, RenewedPolicy
The noun-first convention groups related events together alphabetically and matches domain language ("the order was shipped")
No abbreviations
CustomerIdentityVerified, AmlCheckCompleted
CustIdVerif, AmlChk
Events are permanent records. Abbreviations that make sense today are cryptic 3 years from now when the original team has moved on
No technical prefixes
CreditLimitExceeded, SessionExpired
ON_CREDIT_LIMIT_EXCEEDED, evt:session_expired
Technical prefixes are for messaging infrastructure, not domain events. Events should be readable by domain experts



  PART V
Query Pattern Reference
The canonical queries every event-sourced system needs — with SQL and Python patterns
Query patterns in event-sourced systems fall into two categories: event store queries (direct reads against the events table, used for aggregate reconstruction and audit) and projection queries (reads against read-optimised projection tables). The canonical rule: use projection queries for application features; use event store queries for audit, compliance, and debugging.

  5.1  Event Store Queries — Aggregate Reconstruction  

Query 1 — Load Aggregate Stream (the fundamental query)
Core aggregate load — O(n) without snapshots, O(events since snapshot) with
-- Load all events for an aggregate, in order
SELECT
    event_id, stream_position, event_type, event_version,
    payload, metadata, recorded_at
FROM events
WHERE stream_id = $1
ORDER BY stream_position ASC;

-- With snapshot optimisation (load only events after most recent snapshot)
SELECT e.*
FROM events e
WHERE e.stream_id = $1
  AND e.stream_position > (
    SELECT COALESCE(MAX(stream_position), 0)
    FROM snapshots
    WHERE stream_id = $1
      AND snapshot_version = $2  -- current aggregate snapshot schema version
  )
ORDER BY e.stream_position ASC;


Query 2 — Optimistic Concurrency Append (atomic check + insert)
Optimistic concurrency — uses row-level lock on event_streams, not table lock
-- PostgreSQL: check current version and append in one transaction
BEGIN;

-- Step 1: Lock the stream row and check version
SELECT current_version FROM event_streams
WHERE stream_id = $1
FOR UPDATE;  -- Row-level lock prevents concurrent version updates

-- Step 2: Verify expected version (application layer does this check)
-- if current_version != expected_version: ROLLBACK and raise OptimisticConcurrencyError

-- Step 3: Insert events
INSERT INTO events (stream_id, stream_position, event_type, event_version, payload, metadata)
SELECT $1, current_version + ROW_NUMBER() OVER (ORDER BY ordinal),
       event_type, event_version, payload, metadata
FROM unnest($2::jsonb[]) WITH ORDINALITY AS t(ev, ordinal)
CROSS JOIN LATERAL (
    SELECT ev->>'event_type' AS event_type,
           (ev->>'event_version')::int AS event_version,
           ev->'payload' AS payload,
           ev->'metadata' AS metadata
) AS unpacked;

-- Step 4: Update stream version
UPDATE event_streams
SET current_version = current_version + $3,  -- number of events appended
    updated_at = NOW()
WHERE stream_id = $1;

COMMIT;


Query 3 — Projection Daemon Polling
Daemon polling — use LISTEN/NOTIFY to reduce polling overhead in production
-- Get next batch of events for a projection to process
SELECT
    e.event_id, e.stream_id, e.stream_position,
    e.global_position, e.event_type, e.event_version,
    e.payload, e.metadata, e.recorded_at
FROM events e
WHERE e.global_position > (
    SELECT last_position
    FROM projection_checkpoints
    WHERE projection_name = $1
)
ORDER BY e.global_position ASC
LIMIT $2;  -- batch_size, typically 100-500

-- PostgreSQL LISTEN/NOTIFY for push-based notification (more efficient than polling)
-- In the append transaction:
NOTIFY event_appended, '{"stream_id": "loan-abc", "global_position": 8501}';
-- Projection daemon:
LISTEN event_appended;  -- blocks until notification received, then polls


Query 4 — Temporal Query (state at a specific timestamp)
Temporal query — enables regulatory time-travel and counterfactual analysis
-- Load all events for a stream up to a specific timestamp
-- Used for temporal queries, audit examinations, what-if projections
SELECT
    event_id, stream_position, event_type, event_version,
    payload, metadata, recorded_at
FROM events
WHERE stream_id = $1
  AND recorded_at <= $2  -- the target timestamp
ORDER BY stream_position ASC;

-- Optimised version with snapshot before target timestamp
WITH latest_snapshot AS (
    SELECT stream_position, state
    FROM snapshots
    WHERE stream_id = $1
      AND created_at <= $2
      AND snapshot_version = $3
    ORDER BY stream_position DESC
    LIMIT 1
)
SELECT e.*
FROM events e
LEFT JOIN latest_snapshot ls ON true
WHERE e.stream_id = $1
  AND e.recorded_at <= $2
  AND e.stream_position > COALESCE(ls.stream_position, 0)
ORDER BY e.stream_position ASC;


  5.2  Projection Queries — Application Features  

Query 5 — Causal Chain Traversal (audit and debugging)
Causal chain traversal — recursive CTE following causation_id links
-- Find all events in a causal chain starting from a root correlation_id
-- This is the query that answers: "what led to this decision?"
WITH RECURSIVE causal_chain AS (
    -- Base case: all events with this correlation_id
    SELECT
        event_id, stream_id, event_type, payload, metadata,
        recorded_at, 0 AS depth
    FROM events
    WHERE metadata->>'correlation_id' = $1

    UNION ALL

    -- Recursive: follow causation_id references
    SELECT
        e.event_id, e.stream_id, e.event_type, e.payload, e.metadata,
        e.recorded_at, cc.depth + 1
    FROM events e
    INNER JOIN causal_chain cc
        ON e.event_id::text = cc.metadata->>'causation_id'
    WHERE cc.depth < 20  -- guard against cycles
)
SELECT * FROM causal_chain ORDER BY recorded_at ASC;


Query 6 — Cross-Stream Timeline (regulatory package)
Cross-stream timeline — the basis for generating regulatory packages
-- All events related to a business entity across all streams
-- Used for regulatory examination packages
SELECT
    e.event_id,
    e.stream_id,
    e.event_type,
    e.payload->'application_id' AS application_id,
    e.recorded_at,
    e.metadata->>'agent_id' AS agent_id,
    e.metadata->>'correlation_id' AS correlation_id,
    e.metadata->>'causation_id' AS causation_id
FROM events e
WHERE
    -- Events in the primary application stream
    e.stream_id = $1
    OR
    -- Events in related streams that reference this application
    e.payload->>'application_id' = $2
ORDER BY e.recorded_at ASC, e.global_position ASC;


Query 7 — Projection Lag Monitoring
Lag monitoring — surface as a health endpoint in your MCP server
-- Monitor lag for all projections (run every 60 seconds)
SELECT
    pc.projection_name,
    pc.last_position AS checkpoint_position,
    (SELECT MAX(global_position) FROM events) AS latest_position,
    (SELECT MAX(global_position) FROM events) - pc.last_position AS events_behind,
    EXTRACT(EPOCH FROM (NOW() - pc.updated_at)) * 1000 AS lag_ms,
    CASE
        WHEN EXTRACT(EPOCH FROM (NOW() - pc.updated_at)) > 5 THEN 'CRITICAL'
        WHEN EXTRACT(EPOCH FROM (NOW() - pc.updated_at)) > 1 THEN 'WARNING'
        ELSE 'OK'
    END AS status
FROM projection_checkpoints pc
ORDER BY lag_ms DESC;


Query 8 — Schema Version Distribution (operational health)
Version distribution — run before every schema migration deployment
-- Understand what event_versions are live in production
-- Critical before deploying schema changes or upcasters
SELECT
    event_type,
    event_version,
    COUNT(*) AS event_count,
    MIN(recorded_at) AS oldest,
    MAX(recorded_at) AS newest,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY event_type), 1) AS pct
FROM events
GROUP BY event_type, event_version
ORDER BY event_type, event_version;



  PART VI
Solution Architecture Reference
Pattern templates for common enterprise event sourcing architectures
This section provides architecture templates — reusable patterns that the tutor can use to guide trainees when designing systems. Each pattern includes: the problem it solves, the component structure, the critical design decisions, and the failure modes to guard against.

  Architecture 1 — Single-Service Event Store (The Ledger Pattern)  

The starting pattern for all event sourced systems. One service owns the event store. All writes go through its command handlers. All reads are served from its projections via an MCP server or REST API. This is what trainees build in The Ledger challenge.
COMPONENT
RESPONSIBILITY
TECHNOLOGY
CRITICAL DECISION
Event Store (PostgreSQL)
Append-only storage, optimistic concurrency, global ordering
PostgreSQL 14+ with JSONB, GENERATED ALWAYS identity
Use JSONB not JSON; use global_position GENERATED ALWAYS to prevent application from setting it; BRIN index on recorded_at
Command Handlers
Accept commands, validate against aggregate state, append events
Python asyncio with asyncpg
Load aggregate by replaying stream (or snapshot+replay), not by reading projections; enforce all business invariants before append
Projection Daemon
Rebuild read models from events; maintain checkpoints
Python asyncio background task with PostgreSQL LISTEN/NOTIFY
Checkpoint in same transaction as projection update; every handler must be idempotent; expose lag metric
Upcaster Registry
Transform old event schemas at read time
Python registry pattern; registered by (event_type, from_version)
Register upcasters before any other code runs; test immutability (store not written during upcasting); chain application must be automatic
MCP Server
Expose commands as Tools, projections as Resources
FastMCP or custom MCP server
Resources must read only from projections; Tools must return structured errors; document preconditions for LLM consumers
Outbox Publisher
Deliver events to external buses reliably
Background task polling outbox table with PostgreSQL LISTEN/NOTIFY
Publish at-least-once; consumers must be idempotent; dead-letter after max attempts


  Architecture 2 — Multi-Agent Coordination via Event Store  

Multiple AI agents collaborate on business processes by reading from and writing to shared event streams. No agent communicates directly with another — they coordinate exclusively through events. This is the event-driven equivalent of microservices coordination, applied to AI agent systems.
CONCERN
PATTERN
IMPLEMENTATION
FAILURE MODE TO GUARD AGAINST
Agent isolation
Each agent has its own AgentSession stream; no shared mutable state
stream_id = "agent-{id}-{session_id}" per agent per work session
Agents sharing state via a common writable projection rather than event streams — creates hidden coupling
Work coordination
Work items published as events; agents claim work by appending AgentContextLoaded
Saga coordinates workflow; OptimisticConcurrencyError handles claiming collisions
Two agents claiming the same work item — handled by OCC: first claim wins, second gets OptimisticConcurrencyError and moves to next item
Decision provenance
Every agent decision event references the specific data and model version used
input_data_hash, model_version, model_deployment_id on every decision event
Agent decisions without model version tracking — undetectable when model changes cause decision quality regression
Agent memory on restart
Gas Town pattern: replay AgentSession stream to reconstruct context
AgentContextReconstructor with token budget management
Agent restarts and repeats already-completed work — prevented by checking last_completed_action in reconstructed context
Cross-agent consistency
Saga orchestrator subscribes to all agent decision events and coordinates next step
Saga has its own event stream (saga state); subscribes via projection daemon
Saga state stored only in memory — lost on restart; must be stored in event stream
Concurrent agent access to application
OCC on application stream prevents conflicting decisions
expected_version on every append; retry logic with reload
Retry storms — if many agents collide on the same stream, implement exponential backoff with jitter


  Architecture 3 — Enterprise Integration (Event Store + Kafka)  

The event store is the system of record for one bounded context. Events from the store flow to Kafka for consumption by other services, analytics pipelines, and external systems. The Outbox Pattern guarantees exactly-once write semantics between the store and Kafka.
COMPONENT
ROLE
KEY DESIGN DECISION
Event Store (PostgreSQL)
Source of truth for the bounded context; strong ACID consistency; append-only
Never use Kafka as the event store — Kafka is the integration bus; the store is the source of truth
Outbox Table
Bridge between strong consistency (store) and at-least-once delivery (Kafka)
Write to outbox in same transaction as events table; never write to Kafka directly from command handler
Outbox Publisher
Polls outbox, publishes to Kafka, marks published
Must be idempotent; use Kafka idempotent producer with message key = event_id; dead-letter after max retries
Kafka Topic (domain events)
Carries events to downstream consumers; partitioned by stream_id for ordering
Partition key = stream_id ensures events for one aggregate arrive in order to each consumer
External Projections
Consumer services build their own read models from Kafka topic
Each consumer service has its own checkpoint (Kafka consumer group offset); consumer events are translated at the context boundary via Anti-Corruption Layer
Event Schema Registry
Enforces Avro/Protobuf schema compatibility for Kafka topics
Separate from event_version in the store — Kafka schema compatibility is a transport concern; store versioning is a persistence concern


  Architecture 4 — Greenfield Design Decision Framework  

When a client asks "should we use event sourcing?", this is the decision framework. The tutor should be able to walk trainees through this logic so they can conduct the conversation with a client independently.
FACTOR
STRONG YES
STRONG NO
NUANCED GUIDANCE
Auditability requirement
Regulatory mandate: every decision must be reproducible and tamper-evident
No audit requirement; simple CRUD operations are sufficient
If there is any current or foreseeable compliance requirement, use ES — retrofitting it is extremely expensive
State reconstruction need
Must be able to restore system to any past state for debugging or examination
Current state is the only relevant data; history is never queried
Even if not currently required, ask: "will we ever need to debug a production incident by replaying what happened?"
Business complexity
Complex domain with many state transitions, concurrent processes, rich business rules
Simple domain: create, update, delete a few entity types
Complexity can grow — a system that starts simple can become complex; ES handles this gracefully; CRUD with complex state management does not
Team experience
Team has prior ES or DDD experience; strong engineering discipline
Team has no ES experience; timeline is very short; rapid prototyping phase
The learning curve is real — 4-8 weeks for a team to become productive. Do not adopt ES under tight deadline pressure unless the team is experienced
Data volume
High write volume (>10k events/day); need temporal queries; multiple read models
Low volume; single read model; simple queries
PostgreSQL + ES handles millions of events efficiently; volume alone is not a disqualifier if the architecture is correct
Migration cost
Greenfield or existing system with clean domain model
Legacy system with millions of CRUD records and no domain model; hard deadline
ES migration is one of the most expensive architectural refactors. Always assess migration cost honestly before recommending it for existing systems


The One-Way Door Conversation
The most important thing the tutor must communicate — and the trainee must be able to convey to a client — is this: "Event sourcing is a one-way door. Once you have production events in the store, migration away from event sourcing requires reconstructing current state for every aggregate, building a new CRUD schema from that state, and convincing every downstream system that the new schema is equivalent to the event history. This typically takes 6-18 months and costs more than the original implementation. Make the decision with full awareness of this commitment." A trainee who recommends event sourcing without disclosing this risk is not ready for client-facing work.



  PART VII
Guidance for Mastery: Self-Assessment and Advanced Concepts
Advanced checks and self-development strategies for mastering event sourcing
This section provides diagnostic checks and self-correction strategies to help you reach mastery. The goal is to recognise common pitfalls and apply the correct mental shifts independently.

  7.1  Self-Diagnosis of Experience Level  

Before moving to advanced concepts, diagnose your current understanding. The following questions distinguish a practitioner who has implemented the pattern from one who has only studied it:

QUESTION
NOVICE LEVEL


EXPERIENCED LEVEL


"Name an event in your system that you almost added but decided not to."
Cannot name one; lists events in the catalogue without reflection
Names a specific rejected event; explains why it was a CRUD operation not a domain fact, or why it belonged in a different aggregate
"What is the current event_version of your most-changed event type?"
Does not know; event_version not tracked or always 1
Knows immediately; can recite the upcaster chain; explains what inference decisions were made for historical fields
"What happens to your projections during a deploy?"
Not considered; projections update when the daemon restarts
Describes checkpoint management; discusses whether deploys cause lag spikes; mentions how projection schema migrations are handled
"Your most active stream has 10,000 events. What is the p99 load latency for that aggregate?"
Has not measured; "it's fast"
Has measured or can calculate from snapshot strategy; knows at what event count snapshots become necessary
"How do you detect a rogue agent that is appending events without being authorised?"
Application-layer authorisation check
Structural approach: agent_id in event_stream metadata with authorised_agents list; any append from an unauthorised agent_id is rejected at the store level; audit query to find stream_ids with events from unexpected agent_ids


  7.2  Core Self-Correction Strategies  

Self-Correction 1 — Reframing from State to Fact
When you catch yourself designing events named "UserUpdated", "RecordModified", or "DataChanged":
"Stop. What business thing just happened? Not what the database needs to do — what happened in the domain. A user completed their profile? Their address changed? Each of those is a different event with different consequences. 'Updated' tells you nothing about why."
Refine your thinking: Read your event name as if you're telling a colleague what just happened. If it's too vague, keep pressing until the name communicates intent without reading the payload.

Self-Correction 2 — Testing Concurrency Integrity
When you implement an append without expected_version, or fail to handle OptimisticConcurrencyError:
"Run a collision test. Simulate two concurrent writers trying to append to the same loan application. If both succeed, your system is broken. Optimistic concurrency is not optional; it is the fundamental correctness guarantee."
Remember: without OCC, your event store has no consistency guarantees, and any business logic built on top of it is unstable.

Self-Correction 3 — Validating Checkpoint Reliability
When you design a projection daemon without checkpoint management, or when checkpoints aren't updated atomically:
"Perform a restart test. Kill your daemon process and restart it. If it replays from position 0, your checkpointing is failed. In production, with millions of events, that replay will make your system unusable."
Watching your daemon replay events instead of resuming from the last position is a critical lesson in operational efficiency.

Self-Correction 4 — Thinking About the Schema's Future
Before you finalise any event schema:
"What field am I most likely to need in 6 months? When I add it, I will have to write an upcaster for all historical events. How will I infer that value, and is that inference safe?"
The goal is to develop Schema Immortality Awareness — treating every schema as a permanent contract with your future self.

  7.3  Advanced Practitioner Challenges  

If your technical implementation is solid, your growth lies in three areas: AI-era integration, client communication, and large-scale operations.

Self-Challenge 1 — Proving AI Decision Provenance
If you treat AI actions as opaque results without causal context:
"If you are audited, can you prove which model version made a specific assessment and exactly what data it saw? If not, you do not meet the AI governance requirement."
Extend your event sourcing knowledge to include AI provenance — track model versions and data hashes for every automated decision.

Self-Challenge 2 — Assessing the One-Way Door
Practise your ability to advise on whether a system should adopt event sourcing:
"A client has 3 CRUD databases and wants to migrate to event sourcing in 6 months. Do you say yes? How do you explain the migration cost and the long-term commitment required?"
You must proactively raise migration costs and distinguish between greenfield and legacy scenarios. Principal practitioners know when to say no.

Self-Challenge 3 — Predict Performance Under Load
Move beyond functional design to quantitative analysis:
"If you have 1,000 concurrent aggregates with 4 agents each, what is your expected OCC collision rate? How do you tune your backoff and retry strategy to keep throughput high?"
Mastering performance means being able to predict and manage the overhead of optimistic concurrency in high-volume environments.

Self-Challenge 4 — Designing for Counterfactual Integrity
Prove your expertise by handling complex replay scenarios:
"If you substitute an event in a stream's history, how do you mathematically decide which subsequent events to keep and which to discard? Draw your dependency graph."
You must master the use of causation_id chains to filter histories for counterfactual analysis without contaminating the results.

  7.4  Common Misconceptions — Preemptive Inoculation  

These misconceptions are common. Addressing them early will prevent fundamental implementation mistakes.

MISCONCEPTION
COMMON BELIEF


THE CORRECT UNDERSTANDING
HOW TO SURFACE IT
"Events are messages"
Events are packets of data that flow between services — like Kafka messages
Events are facts stored permanently in a database. They do not flow anywhere by default. The Outbox Pattern is how they flow.
Check: "If I turn off my message broker, does my event store still work?" The answer must be yes.


"I can fix old events"
When a bug is found in historical data, the solution is to UPDATE the events table
Compensating events are the only mechanism for correcting history. The original event is permanent evidence.
Practise by deliberately introducing a "wrong" event in a test and implementing a compensating event to correct it.


"Projections are optional"
The event store is the database; application features can just query the events table directly
Querying the events table for application features creates tight coupling to the event schema and is O(n) for every feature request
Try running a feature without a projection. Measure the performance and then consider the cost at 1,000 requests per second.


"Every event needs a snapshot"
Snapshots are a core part of event sourcing that must be implemented from day one
Snapshots are a performance optimisation for high-volume streams. Start without them. Add them when load testing reveals unacceptable latency.
Check your longest stream count. If it's <1,000, snapshots are premature. Mastery requires "measure first" discipline.


"Event sourcing is eventually consistent"
The entire event sourcing system is eventually consistent
The event store (write side) is strongly consistent. Only async projections (read side) are eventually consistent. Command handlers read from strongly consistent aggregate state.
Ask: "If I append and immediately load the stream, do I see the event?" The answer must be yes.


"Aggregate = database table"
The aggregate in event sourcing corresponds to a database table
An aggregate is a consistency boundary, not a storage unit. Multiple instances of the same aggregate type share no mutable state — each has its own stream.
Map it out: aggregate type → one independent stream per instance. No shared mutable state.







TRP1 FDE Program  ·  Event Sourcing Practitioner Manual  ·  March 2026  ·  Confidential Practitioner Resource


TRP1 FDE PROGRAM  ·  ARC 5–6  ·  Week 5
The Ledger
Agentic Document-to-Decision Platform
Two weeks. Five real LangGraph agents. GAAP financial documents. A full event-sourced loan decisioning pipeline — from uploaded PDF to auditable approval or decline.

  SECTION 1  ·  WHAT YOU ARE BUILDING AND WHY

"Apex Financial Services processes 40–80 commercial loan applications per week. Applicants upload financial statements. AI agents read them, reason about them, and record every decision as an immutable event. Nothing is lost. Everything is auditable. You are building the infrastructure that makes this possible."

This is not a textbook exercise. The system you build has five components that must interlock correctly — and you do not control the order in which they break.

COMPONENT
WHAT IT IS
WHERE ITS DATA LIVES
YOUR JOB
Applicant Registry
A read-only PostgreSQL CRM. 80 companies, 3 years of GAAP financials, compliance flags, loan history.
External schema: applicant_registry.*Never written by the event store system.
Query it (read-only) from agents. Never append to it.
Document Corpus
160+ files per 80 applicants: income statement PDF, balance sheet PDF, multi-year Excel workbook, flat CSV. All GAAP-formatted. Generated by the data generator.
Filesystem: documents/{company_id}/File paths recorded in DocumentUploaded events.
Plug your Week 3 extraction pipeline into DocumentProcessingAgent.
Event Store
Append-only PostgreSQL table. Seven aggregate stream types. ~3,500+ events by end of the project.
Event store schema: events, event_streams, outbox, snapshots, projection_checkpoints.The single source of truth for all application lifecycle decisions.
Implement EventStore.append(), load_stream(), load_all(). Every agent and projection depends on this.
LangGraph Agents
Five compiled StateGraph agents. Every node execution, every LLM call, every tool call recorded as an event in the agent's session stream.
Agent session streams: agent-{type}-{session_id}Output streams: loan-*, docpkg-*, credit-*, fraud-*, compliance-*
Implement the four stub agents following the CreditAnalysisAgent reference pattern.
Projections + MCP
Three read-model projections rebuilt from the event stream. MCP server exposes 8 tools (commands) and 6 resources (projection queries).
Projection tables in the same PostgreSQL database.MCP served locally on port 8765.
Build ProjectionDaemon and three projections. Expose via FastMCP.


The Two Non-Negotiable Design Rules
Before writing a single line of agent code, internalise these two rules. Every architectural decision in this system flows from them.

Rule 1: The Data Boundary
The Applicant Registry is a read-only external system. Agents query it; they never write to it. Historical financial data, compliance flags, and company profiles live there because they existed before any loan application was submitted. The event store captures only what happens during the application lifecycle — everything from submission to decision. If you find yourself wanting to write to the Applicant Registry from an agent, you have misunderstood the boundary.


Rule 2: Gas Town — Session Start Before Any Work
Every agent appends AgentSessionStarted as the very first event, before any data is loaded or any decision is made. This is the Gas Town pattern: the session stream is the agent's memory. On crash recovery, a new agent instance replays its session stream to reconstruct context and resume from the last successful node — without redoing completed work. An agent that starts work before appending AgentSessionStarted cannot recover from a crash.



  SECTION 2  ·  THE CANONICAL EVENT SCHEMA — ALL 7 AGGREGATES

All 45 event types are defined in ledger/schema/events.py. That file is the single source of truth. Every agent, every test, every projection imports from there. Never redefine event classes elsewhere.
The data generator (datagen/event_simulator.py) simulates all 45 event types for seed applications and validates every generated event against EVENT_REGISTRY before writing to the database. If your schema changes, the generator catches it immediately.

STREAM PREFIX
AGGREGATE
KEY EVENTS (in lifecycle order)
WHO WRITES
loan-{id}
LoanApplication
ApplicationSubmitted · DocumentUploadRequested · DocumentUploaded · CreditAnalysisRequested · FraudScreeningRequested · ComplianceCheckRequested · DecisionRequested · DecisionGenerated · HumanReviewRequested · HumanReviewCompleted · ApplicationApproved · ApplicationDeclined
Command handlers + agents (as side-effects of completing work)
docpkg-{id}
DocumentPackage
PackageCreated · DocumentAdded · DocumentFormatValidated · ExtractionStarted · ExtractionCompleted · QualityAssessmentCompleted · PackageReadyForAnalysis
DocumentProcessingAgent exclusively
agent-{type}-{session_id}
AgentSession
AgentSessionStarted · AgentInputValidated · AgentInputValidationFailed · AgentNodeExecuted (one per LangGraph node) · AgentToolCalled (one per registry/store query) · AgentOutputWritten · AgentSessionCompleted · AgentSessionFailed · AgentSessionRecovered
Each agent writes to its own session stream
credit-{id}
CreditRecord
CreditRecordOpened · HistoricalProfileConsumed · ExtractedFactsConsumed · CreditAnalysisCompleted · CreditAnalysisDeferred
CreditAnalysisAgent exclusively
fraud-{id}
FraudScreening
FraudScreeningInitiated · FraudAnomalyDetected (0–N) · FraudScreeningCompleted
FraudDetectionAgent exclusively
compliance-{id}
ComplianceRecord
ComplianceCheckInitiated · ComplianceRulePassed/Failed/Noted (one per rule) · ComplianceCheckCompleted
ComplianceAgent exclusively
audit-{entity_type}-{id}
AuditLedger
AuditIntegrityCheckRun (with SHA-256 hash chain)
Audit chain builder (Phase 4)


The AgentSession Stream — One Event Per LangGraph Node
This is the most important structural requirement of the system. Every time a LangGraph node executes, your agent must append an AgentNodeExecuted event to its session stream. This means the session stream is a complete, node-by-node record of the agent's execution — suitable for regulatory examination, crash recovery, and cost attribution.

EVENT TYPE
WHEN APPENDED
KEY FIELDS
REQUIRED?
AgentSessionStarted
First — before any data loaded or decision made. Gas Town anchor.
session_id, agent_type, model_version, context_source ("fresh" or "prior_session_replay:{id}"), context_token_count
REQUIRED — every session
AgentInputValidated
After validate_inputs node succeeds.
inputs_validated (list of what was checked), validation_duration_ms
REQUIRED — every session
AgentInputValidationFailed
If validate_inputs finds missing or invalid inputs.
missing_inputs (list), validation_errors (list)
Required when inputs are invalid
AgentNodeExecuted
At the END of every node. One per node per session.
node_name, node_sequence, input_keys, output_keys, llm_called, llm_tokens_input, llm_tokens_output, llm_cost_usd, duration_ms
REQUIRED — every node
AgentToolCalled
After every call to the Applicant Registry or event store (as a query tool).
tool_name, tool_input_summary (condensed), tool_output_summary (condensed), tool_duration_ms
Required per tool call
AgentOutputWritten
After write_output node appends all domain events.
events_written (list of {stream_id, event_type, stream_position}), output_summary
REQUIRED — every session
AgentSessionCompleted
Last event — after all work is done.
total_nodes_executed, total_llm_calls, total_tokens_used, total_cost_usd, next_agent_triggered
REQUIRED — every session
AgentSessionFailed
On unrecoverable error.
error_type, error_message, last_successful_node, recoverable (bool)
Required on failure
AgentSessionRecovered
First event of a recovery session.
recovered_from_session_id, recovery_point (node name where resumed)
Required on recovery



  SECTION 3  ·  THE DATA GENERATOR — RUN FIRST, EVERYTHING DEPENDS ON IT

The data generator is a full deliverable. It creates three distinct datasets before any agent runs: the Applicant Registry database, the Document Corpus, and the seed event history. Run it once on Day 1. If it exits with code 0, your environment is ready.

# Run once. Idempotent — safe to re-run (ON CONFLICT DO NOTHING everywhere).
python datagen/generate_all.py \
    --applicants 80 \
    --db-url postgresql://localhost/apex_ledger \
    --docs-dir ./documents \
    --output-dir ./data \
    --random-seed 42

# Expected output (abridged):
# [1/5] Generating 80 company profiles...
#   [OK] GROWTH:20, STABLE:25, DECLINING:12, RECOVERING:13, VOLATILE:10
#   [OK] LOW:24, MEDIUM:33, HIGH:23  |  With compliance flags: 8
# [2/5] Generating financial documents...
#   [OK] 320 files in ./documents/  (80 income PDFs + 80 balance PDFs + 80 Excel + 80 CSV)
# [3/5] Simulating seed event history (29 applications)...
#   [OK] 1,847 events across 29 applications validated
# [4/5] Schema validation: 1847 validated, 0 errors
# [5/5] Writing to database...
#   [OK] Database write complete
# GENERATION COMPLETE in 4m 18s


What the Generator Creates
DATASET
FILES / TABLES
COUNT
PURPOSE
Applicant Registry
applicant_registry.companiesapplicant_registry.financial_historyapplicant_registry.compliance_flagsapplicant_registry.loan_relationships
80 companies240 financial rows (3yr each)~8 flag rows~48 loan rows
Read-only source of company profiles and historical financials. Agents query this; never write to it.
GAAP PDF — Income Statement
documents/{company_id}/income_statement_2024.pdf
80 PDFs in 4 variants: clean (40), dense/multi-subtotal (20), missing-EBITDA (8), scanned-quality (12)
Primary input to Week 3 extraction pipeline. Each variant exercises a different extraction challenge.
GAAP PDF — Balance Sheet
documents/{company_id}/balance_sheet_2024.pdf
80 PDFs. 6 intentionally contain minor equity rounding discrepancy ($500–$4,500).
Tests balance_sheet_balances validation. DocumentProcessingAgent must flag discrepancies.
Excel Workbook
documents/{company_id}/financial_statements.xlsx
80 workbooks. 4 sheets: Income Statement, Balance Sheet, Key Ratios, and a 3-year comparison.
Alternative format input. DocumentProcessingAgent can process .xlsx as well as PDF.
Application Proposal PDF
Generated per application (not per company)
One per seeded application
Contains company narrative, loan purpose, use of proceeds, GAAP financial highlights. Tests the APPLICATION_PROPOSAL document type.
Flat CSV
documents/{company_id}/financial_summary.csv
80 CSVs (most recent fiscal year only)
Quick programmatic consumption of financials. Useful for registry cross-reference checks in FraudDetectionAgent.
Seed Events (JSONL)
data/seed_events.jsonl + database
1,847 events across 29 applications
Full realistic event history for 29 applications in 9 lifecycle states. Simulates all 5 LangGraph agents including per-node AgentNodeExecuted events. Validates the complete schema before you write any real agent code.


Seed Application Distribution (29 applications)
APPLICATION IDs
STATE
COUNT
WHAT AGENTS CAN DO WITH THEM
APEX-0001 – APEX-0006
SUBMITTEDDocuments requested, nothing uploaded
6
Upload documents via MCP tool. Tests DocumentUploadRequested → DocumentUploaded flow.
APEX-0007 – APEX-0011
DOCUMENTS_UPLOADEDDocs on disk, Week 3 not run
5
Run DocumentProcessingAgent immediately. Tests the standard entry path.
APEX-0012 – APEX-0015
DOCUMENTS_PROCESSEDFacts extracted, credit not started
4
Run CreditAnalysisAgent. FinancialFacts already in events — no extraction needed.
APEX-0016 – APEX-0018
CREDIT_COMPLETECredit done, fraud pending
3
Run FraudDetectionAgent. Tests mid-lifecycle agent pickup.
APEX-0019 – APEX-0020
FRAUD_COMPLETEFraud done, compliance not started
2
Run ComplianceAgent. Tests compliance evaluation on a live stream.
APEX-0021 – APEX-0025
APPROVED (4) + DECLINED (1)
5
Projections must reflect terminal states correctly from Day 1.
APEX-0026 – APEX-0027
DECLINEDAgent-driven credit decline
2
Tests decline path. adverse_action_notice_required=True on ApplicationDeclined.
APEX-0028
DECLINED_COMPLIANCEMontana company — REG-003 hard block
1
Tests compliance hard block. No DecisionGenerated should ever appear.
APEX-0029
REFERREDLow-confidence orchestrator decision
1
Tests human review path. HumanReviewCompleted command handler must work on this.


The Simulator Validates Your Schema
The event simulator (datagen/event_simulator.py) mirrors exactly what real LangGraph agents produce: the same event types, the same field names, the same causal chains, the same AgentNodeExecuted sequence per agent. If the simulator runs clean (0 schema errors), your schema is correctly implemented and your real agents will be able to write to it. Run: python datagen/generate_all.py --validate-only to check schema without writing to the database.



  SECTION 4  ·  THE FIVE LANGGRAPH AGENTS

Every agent is a compiled LangGraph StateGraph. Every agent inherits from BaseApexAgent (ledger/agents/base_agent.py), which provides Gas Town session management, per-node event recording, tool call recording, OCC retry scaffolding, and LLM cost tracking. You implement the nodes; the base class handles everything else.

The Reference Implementation
CreditAnalysisAgent (ledger/agents/credit_analysis_agent.py) is the complete reference implementation. It demonstrates: build_graph() with a 6-node StateGraph, each node calling self._record_node_execution() at its end, the LLM call pattern via self._call_llm(), the OCC retry pattern in write_output, and how to trigger the next agent. Implement the remaining 4 agents by following this pattern exactly.


Node Sequence — All Agents Follow This Pattern
# Every agent has this node sequence (domain nodes vary):

validate_inputs → open_aggregate_record → load_external_data → [domain nodes] → write_output

# validate_inputs:      Check application state, verify prerequisites exist
# open_aggregate_record: Create the agent's output aggregate stream (e.g. CreditRecordOpened)
# load_external_data:   Query Applicant Registry AND load from event store
# [domain nodes]:       The reasoning work — usually one LLM call node + one policy node
# write_output:         Append output events with OCC retry; trigger next agent

# At the END of EVERY node, call:
await self._record_node_execution(
    node_name="my_node",
    input_keys=["key1", "key2"],       # state keys consumed
    output_keys=["result_key"],        # state keys produced
    duration_ms=int((time.time()-t0)*1000),
    llm_tokens_input=tok_in,           # None if no LLM call
    llm_tokens_output=tok_out,
    llm_cost_usd=cost,
)

# For every registry or event store query, call:
await self._record_tool_call(
    tool="query_applicant_registry",
    inp=f"company_id={applicant_id}",
    out=f"Loaded 3yr financials, {n} flags",
    ms=duration_ms,
)



Agent 1 — DocumentProcessingAgent (stub_agents.py)
Wraps the Week 3 Document Intelligence pipeline. Takes uploaded PDFs, runs extraction, assesses quality with the LLM, and appends extraction events to the docpkg stream. The LLM's role is quality assessment only — it checks coherence, not creditworthiness.
NODE
READS FROM
WRITES TO STORE
LLM?
validate_inputs
LoanApplication stream (state must be DOCUMENTS_UPLOADED)
AgentInputValidated
No
validate_document_formats
Filesystem (check files exist, check format)
DocumentFormatValidated per document
No
extract_income_statement
PDF file via Week 3 pipeline
ExtractionStarted, ExtractionCompleted (with FinancialFacts)
No (pipeline handles)
extract_balance_sheet
PDF file via Week 3 pipeline
ExtractionStarted, ExtractionCompleted (with FinancialFacts)
No
assess_quality
Extracted FinancialFacts from both documents
QualityAssessmentCompleted, PackageReadyForAnalysis
YES — checks coherence, flags anomalies
write_output
State dict (decisions complete)
CreditAnalysisRequested on loan stream (triggers next agent)
No


Week 3 integration: In _node_extract_income_statement(), call your Week 3 pipeline directly: from document_refinery.pipeline import extract_financial_facts. The extracted FinancialFacts struct goes directly into the ExtractionCompleted event payload. If extraction produces None for any critical field, set field_confidence[field] = 0.0 and add to extraction_notes — do not default to zero.

# Quality assessment LLM prompt (implement in _node_assess_quality):
QUALITY_SYSTEM_PROMPT = """
You are a financial document quality analyst. You receive structured data
extracted from a company's financial statements.

Check ONLY:
1. Internal consistency (Gross Profit = Revenue - COGS, Assets = Liabilities + Equity)
2. Implausible values (margins > 80%, negative equity without note)
3. Critical missing fields (total_revenue, net_income, total_assets, total_liabilities)

Return JSON: {"overall_confidence": float, "is_coherent": bool,
  "anomalies": [str], "critical_missing_fields": [str],
  "reextraction_recommended": bool, "auditor_notes": str}

DO NOT make credit or lending decisions. DO NOT suggest loan outcomes.
"""



Agent 2 — CreditAnalysisAgent (credit_analysis_agent.py — REFERENCE)
The complete reference implementation. Read it before implementing any other agent. Six nodes. One LLM call (analyze_credit_risk node). Two data sources: Applicant Registry (historical financials via registry client) and event store (extracted facts from docpkg stream). Hard policy constraints enforced in Python after the LLM call — the LLM cannot override them.
POLICY RULE
ENFORCED IN
WHAT IT DOES
Max loan-to-revenue ratio: 35%
apply_policy_constraints node (Python)
Reduces recommended_limit_usd if it exceeds annual_revenue × 0.35. LLM recommendation is overridden.
Prior default → risk_tier = HIGH
apply_policy_constraints node (Python)
Forces risk_tier to HIGH regardless of LLM output if any loan_relationship has default_occurred=True.
Active HIGH compliance flag → confidence ≤ 0.50
apply_policy_constraints node (Python)
Caps confidence at 0.50. Combined with the orchestrator's confidence < 0.60 → REFER rule, this guarantees human review.
confidence < 0.60 → REFER
LoanApplicationAggregate.assert_valid_orchestrator_decision() (aggregate enforces)
The aggregate rejects DecisionGenerated with recommendation=APPROVE if confidence < 0.60. The orchestrator cannot override this.


Agent 3 — FraudDetectionAgent (stub_agents.py)
Detects inconsistencies between submitted documents and what the bank already knows. Reads extracted FinancialFacts from the event store AND historical financials from the Applicant Registry. The LLM identifies pattern anomalies; Python computes the fraud_score from weighted anomalies.
NODE
KEY LOGIC
load_facts
Load ExtractionCompleted events from docpkg-{id}. Get current-year FinancialFacts.
cross_reference_registry
Load 3yr financial_history from Applicant Registry. Compute deltas: current vs prior year for revenue, EBITDA, margins.
analyze_fraud_patterns
LLM call: "Given extracted current-year figures and 3-year history, identify anomalous gaps." Returns list of FraudAnomaly objects each with anomaly_type, description, severity, evidence. fraud_score = sum(severity_weights). Score > 0.60 → DECLINE. Score 0.30–0.60 → FLAG_FOR_REVIEW.
write_output
Append FraudScreeningCompleted on fraud stream. Append ComplianceCheckRequested on loan stream.


Agent 4 — ComplianceAgent (stub_agents.py)
Evaluates 6 regulatory rules in sequence. Rules are deterministic Python — no LLM in the decision path. LLM is used only in the write_output node to generate human-readable evidence summaries. A hard block (is_hard_block=True) stops rule evaluation immediately — no further rules are checked.
RULE ID
RULE NAME
HARD BLOCK?
WHAT TO CHECK
REG-001
Bank Secrecy Act Check
No (remediable)
company has no compliance_flag with flag_type=AML_WATCH AND is_active=True
REG-002
OFAC Sanctions Screening
YES
company has no compliance_flag with flag_type=SANCTIONS_REVIEW AND is_active=True
REG-003
Jurisdiction Lending Eligibility
YES
company.jurisdiction != "MT" (Montana excluded for this exercise)
REG-004
Legal Entity Type Eligibility
No (remediable)
NOT (legal_type=="Sole Proprietor" AND requested_amount_usd > 250000)
REG-005
Minimum Operating History
YES
(2026 - company.founded_year) >= 2
REG-006
CRA Community Reinvestment Act
No (informational)
Always NOTED (not passed/failed). Append ComplianceRuleNoted with note_type="CRA_CONSIDERATION".


# ComplianceAgent node pattern — deterministic rules, no LLM in decision path

# build_graph() uses conditional edges to stop after hard block:
graph.add_node("evaluate_reg001", self._node_evaluate_reg001)
graph.add_node("evaluate_reg002", self._node_evaluate_reg002)
# ...
graph.add_conditional_edges(
    "evaluate_reg001",
    lambda s: "hard_block" if s.get("hard_block") else "evaluate_reg002",
    {"evaluate_reg002": "evaluate_reg002", "hard_block": "write_output"}
)

# Each rule node follows this pattern:
async def _node_evaluate_reg003(self, state):
    t0 = time.time()
    company = state["company_profile"]
    passes = company.jurisdiction != "MT"
    await self._append_compliance_result(state, "REG-003", "Jurisdiction Check", passes, is_hard=True)
    await self._record_node_execution("evaluate_reg003", [...], [...], ms=...)
    return {**state, "hard_block": not passes, "rules_evaluated": state["rules_evaluated"] + 1}



Agent 5 — DecisionOrchestratorAgent (stub_agents.py)
The only agent that reads from other agents' output streams. Synthesises credit, fraud, and compliance results into a final recommendation. Hard constraints enforced in Python after the LLM synthesises the executive summary. The recommendation may be overridden by constraints; the summary always explains why.
NODE
READS FROM
OUTPUT
load_credit
credit-{id} stream: CreditAnalysisCompleted
risk_tier, recommended_limit, confidence, rationale, data_quality_caveats
load_fraud
fraud-{id} stream: FraudScreeningCompleted
fraud_score, risk_level, anomalies_found, recommendation
load_compliance
compliance-{id} stream: ComplianceCheckCompleted
overall_verdict (CLEAR/BLOCKED/CONDITIONAL), has_hard_block
synthesize_decision
All loaded analysis data
LLM call: produce executive_summary (3–5 sentences), key_risks (list), initial recommendation. Returns OrchestratorDecision JSON.
apply_hard_constraints
OrchestratorDecision + loaded data
Python rules: compliance BLOCKED → force DECLINE. confidence < 0.60 → force REFER. fraud_score > 0.60 → force REFER. Overrides LLM recommendation if needed.
write_output
Final decision
DecisionGenerated on loan stream. ApplicationApproved or ApplicationDeclined if auto. HumanReviewRequested if REFER.



  SECTION 5  ·  TECHNOLOGY STACK

COMPONENT
PACKAGE
VERSION
WHY — NOT THE ALTERNATIVE
LangGraph (agent graphs)
langgraph
>=0.2
Compiled StateGraph gives explicit node sequences, conditional edges, and built-in async support. Do NOT use bare asyncio task loops — the graph structure is what makes crash recovery possible.
LLM API
anthropic
>=0.30
Direct SDK. No LangChain wrappers. You need to see raw token counts (response.usage) for cost attribution. Always use AsyncAnthropic for the async node pattern.
Event store DB driver
asyncpg
>=0.29
Native PostgreSQL protocol. Non-blocking. Fastest Python Postgres driver. NOT psycopg2 (blocking) or SQLAlchemy ORM (hides the schema).
Event/agent schemas
pydantic
>=2.6
All event payloads, agent state, registry query results are Pydantic v2 BaseModel. Validation is not optional. Use model_dump(mode="json") for serialisation.
MCP server
fastmcp
>=0.9
Decorator-based MCP server. @mcp.tool() for commands, @mcp.resource() for projection queries.
PDF generation (datagen)
reportlab
>=4.2
For generating the 160 financial statement PDFs. Only needed in datagen/.
PDF extraction (agents)
Your Week 3 pipeline
MinerU or Docling
Reuse your Week 3 implementation exactly. DocumentProcessingAgent wraps it.
Excel generation/parsing
openpyxl
>=3.1
For generating .xlsx files and for DocumentProcessingAgent to parse .xlsx uploads.
Fake data generation
faker
>=24
Company names, EINs, addresses. Used only in datagen/.
Testing
pytest + pytest-asyncio
>=8.0, >=0.23
asyncio_mode = auto in pytest.ini — all async tests work without @pytest.mark.asyncio.


# requirements.txt — pin everything
asyncpg>=0.29.0,<0.30
anthropic>=0.30.0,<0.40
pydantic>=2.6.0,<3.0
langgraph>=0.2.0,<0.3
fastmcp>=0.9.0,<1.0
reportlab>=4.2.0,<5.0
openpyxl>=3.1.0,<4.0
faker>=24.0.0,<25.0
python-dotenv>=1.0.0,<2.0
pytest>=8.0.0,<9.0
pytest-asyncio>=0.23.0,<0.24
# Your Week 3 deps (add whichever you used):
# mineru>=1.0  OR  docling>=2.0

# pytest.ini
[pytest]
asyncio_mode = auto

# .env (never commit)
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://localhost/apex_ledger
DOCUMENTS_DIR=./documents
REGULATION_VERSION=2026-Q1
LOG_LEVEL=INFO



apex-ledger/
├── .env                          # Never committed
├── pytest.ini                    # asyncio_mode = auto
├── requirements.txt
├── DOMAIN_NOTES.md               # 6 required questions answered before Day 2
├── DESIGN.md                     # 6 required sections — completed Day 10
├── DATA_GENERATION.md            # Simulator rules, PDF variants, event counts, API costs
│
├── datagen/                      # Data generator (provided — do not modify core logic)
│   ├── generate_all.py           # Main entry point
│   ├── company_generator.py      # 80 companies with GAAP financials
│   ├── pdf_generator.py          # GAAP PDF income statement + balance sheet
│   ├── excel_generator.py        # Multi-sheet GAAP Excel workbook
│   ├── event_simulator.py        # Full agent event simulation for seeding
│   └── schema_validator.py       # Validates all events against EVENT_REGISTRY
│
├── ledger/                       # Your application package
│   ├── schema/events.py          # Canonical event schema (provided — 45 event types)
│   ├── event_store.py            # EventStore (implement) + InMemoryEventStore (provided)
│   ├── upcasters.py              # UpcasterRegistry (provided + 2 upcasters to implement)
│   ├── domain/aggregates/        # LoanApplicationAggregate (stub — implement apply())
│   ├── projections/              # ProjectionDaemon + 3 projection classes (stub)
│   ├── agents/
│   │   ├── base_agent.py         # BaseApexAgent (provided)
│   │   ├── credit_analysis_agent.py  # Reference implementation (provided)
│   │   └── stub_agents.py        # 4 agent stubs (implement)
│   ├── registry/client.py        # ApplicantRegistryClient (stub — implement)
│   └── mcp_server.py             # FastMCP server (stub — implement Phase 5)
│
├── documents/                    # Generated files (gitignored, regenerable)
├── tests/
│   ├── conftest.py               # Fixtures using InMemoryEventStore
│   ├── phase1/test_event_store.py  # EventStore tests (10 provided — use InMemoryEventStore)
│   ├── test_schema_and_generator.py  # Phase 0 schema tests (10 provided — all pass)
│   ├── test_event_store.py         # Real DB tests (skip until EventStore implemented)
│   ├── test_narratives.py          # 5 narrative tests (skipped — implement after agents)
│   └── phase2-5/                   # Implement phase by phase
└── scripts/
    ├── run_pipeline.py             # Process one application end-to-end
    └── demo_narr05.py              # Required demo script (Day 10)




  SECTION 6  ·  TEN-DAY IMPLEMENTATION PLAN

Days 1–5 build the foundation: data generation, event store, and document processing. No LLM calls until Day 5. Days 6–10 layer on the real agents, projections, and production quality. Day 10 is exclusively for DESIGN.md, demo, and submission packaging.

  WEEK 1 — FOUNDATION  

DAY
FOCUS
DELIVERABLE BY END OF DAY
GATE TEST
Day 1Mon
Run the data generator.Study the seed events.Write DOMAIN_NOTES.md.
80 companies in applicant_registry schema.160 PDFs + 80 Excel + 80 CSV in documents/.1,847 seed events in event store.DOMAIN_NOTES.md: all 6 questions answered.
python datagen/generate_all.py exits 0.python datagen/generate_all.py --validate-only: 0 errors.psql: SELECT count(*) FROM events; → 1847.
Day 2Tue
Implement EventStore:stream_version() → append() → load_stream() → load_all().All in a single transaction with OCC.
EventStore passes the provided real-DB test suite.InMemoryEventStore already passes phase1 tests — confirm your real implementation matches.
pytest tests/test_event_store.py -v (requires DB).All 10 pass.Key: test_concurrent_double_append_exactly_one_succeeds.
Day 3Wed
Implement LoanApplicationAggregate.apply() for all event types.Implement ApplicantRegistryClient (4 query methods).Implement DocumentProcessingAgent (6 nodes).
DocumentProcessingAgent.process_application("APEX-0007") runs end to end.Docpkg stream has ExtractionCompleted events with non-null total_revenue and net_income.AgentNodeExecuted events appear in agent session stream.
python scripts/run_pipeline.py --app APEX-0007 --phase documentExtractionCompleted event in docpkg stream.QualityAssessmentCompleted.is_coherent = True.CreditAnalysisRequested event in loan stream.
Day 4Thu
Implement CreditAnalysisAgent (reference provided — study it first).Implement FraudDetectionAgent.
Credit + Fraud run on APEX-0012 through APEX-0018.CreditAnalysisCompleted events have non-empty rationale and valid confidence.FraudScreeningCompleted events in fraud streams.
python scripts/run_pipeline.py --app APEX-0012 --phase creditCreditAnalysisCompleted.confidence between 0.55 and 0.95.CreditAnalysisCompleted.decision.risk_tier is LOW/MEDIUM/HIGH.pytest tests/phase2/ (implement these tests).
Day 5Fri
Implement ComplianceAgent and DecisionOrchestratorAgent.NARR-01 (OCC collision) and NARR-04 (Montana compliance block) should now pass.
All 5 agents working.At least 5 applications reach APPROVED or DECLINED state.NARR-01 and NARR-04 pass.
pytest tests/test_narratives.py::test_narr01 tests/test_narratives.py::test_narr04Both pass.psql: SELECT state, count(*) FROM ... (your projection or direct query).


  WEEK 2 — AGENTS, PROJECTIONS, PRODUCTION QUALITY  

DAY
FOCUS
DELIVERABLE BY END OF DAY
GATE TEST
Day 6Mon
Implement ProjectionDaemon and all 3 projections.NARR-02 (document extraction failure with missing EBITDA) should pass.
All 3 projections rebuild from seed events correctly.ApplicationSummary shows correct counts for all 29 seeded applications.NARR-02 passes.
pytest tests/test_narratives.py::test_narr02ApplicationSummary projection shows 8 APPROVED, 3 DECLINED, 1 DECLINED_COMPLIANCE, 1 REFERRED from seed data.
Day 7Tue
Implement crash recovery (NARR-03).Implement HumanReviewCompleted command handler (NARR-05).Run load generator — measure projection lag.
All 5 narrative tests passing.Load generator: 15 concurrent applications, 6 workers, 0 unresolved OCC collisions.Projection lag < 800ms under load.
pytest tests/test_narratives.py — all 5 pass.python load_gen/run_concurrent.py --applications 15 --concurrency 6→ occ_collision_report.txt: 10–35 collisions, all resolved.
Day 8Wed
Implement upcasters (Phase 4).Build audit integrity chain (AuditIntegrityCheckRun with SHA-256 chain).Implement AgentContextReconstructor for Gas Town recovery.
UpcasterRegistry has both required upcasters.Immutability test passes (upcast does not modify DB row).Audit chain for APEX-0021 verifiable independently.
pytest tests/phase4/Key: test_upcaster_does_not_write_to_events_tabletest_audit_chain_is_independently_verifiable
Day 9Thu
Implement MCP server: 8 tools + 6 resources.Full lifecycle integration test via MCP only (12 assertions).
MCP server running on port 8765.All 8 tools callable.All 6 resources return projection data.Full lifecycle test passes.
pytest tests/phase5/test_full_lifecycle_via_mcp.py12 assertions pass.Key: application reaches APPROVED state having used only MCP tools.
Day 10Fri
DESIGN.md (all 6 sections).python scripts/demo_narr05.py — runs under 90 seconds.api_cost_report.txt generated.Submission folder packaged.
DESIGN.md complete.demo_narr05.py runs cleanly.regulatory_package_NARR05.json passes verify_package.py.All required artifacts in artifacts/.
python tests/phase6/verify_package.py artifacts/regulatory_package_NARR05.jsonpytest tests/ -q → 0 failures (skipped DB tests excluded).


If You Finish Early
Phase 6 bonus: WhatIfProjector (replay NARR-05 event history with substituted credit decision) and generate_regulatory_package() (self-contained, independently verifiable JSON audit package). Phase 6 is the Score 5 qualifier. Without it, maximum score on any criterion is 4. Attempt Phase 6 only after all 5 narrative tests pass and DESIGN.md is complete.



  SECTION 7  ·  THE FIVE NARRATIVE SCENARIOS

These five applications are not in the seed data. You generate them by running your agents against companies from the Applicant Registry. Each tests a production failure mode. The automated test harness checks the exact event sequence. Passing all five is the primary correctness gate for the challenge.

NARR-01 — Concurrent OCC Collision
FIELD
SPECIFICATION
Company
COMP-031 — manufacturing sector, MEDIUM risk, revenue ~$3.8M
Trigger
Two CreditAnalysisAgent instances are started simultaneously on NARR-01 after documents are processed. Both read the credit stream at version 0 (CreditRecordOpened only).
Expected sequence
Agent A appends CreditAnalysisCompleted at expected_version=0 (succeeds → stream version becomes 1). Agent B hits OptimisticConcurrencyError, reloads the stream, sees Agent A's result, confirms analysis is still needed (it is — Agent A's result is for the same application), appends its own CreditAnalysisCompleted at expected_version=1 (succeeds → version becomes 2). Both agents complete without raising to the caller.
Test assertions
credit stream has exactly 2 CreditAnalysisCompleted events. stream_position 1 and 2 both have event_type=CreditAnalysisCompleted. No unhandled exceptions in agent logs. Second event's metadata["causation_id"] is resolvable.


NARR-02 — Document Extraction Failure (Missing EBITDA)
FIELD
SPECIFICATION
Company
COMP-044 — healthcare sector, STABLE trajectory, income statement PDF is the missing_ebitda variant
Trigger
DocumentProcessingAgent processes NARR-02 and encounters a PDF with no EBITDA line item.
Expected sequence
ExtractionCompleted has facts.ebitda=None and field_confidence["ebitda"]=0.0 and "ebitda" in extraction_notes. QualityAssessmentCompleted has "ebitda" in critical_missing_fields. CreditAnalysisAgent receives the quality flags, notes data_quality_caveats in its output, and caps confidence at 0.75. Application continues — it is not blocked.
Test assertions
ExtractionCompleted.payload.facts["ebitda"] is None. QualityAssessmentCompleted.payload.critical_missing_fields contains "ebitda". CreditAnalysisCompleted.payload.decision["confidence"] <= 0.75. CreditAnalysisCompleted.payload.decision["data_quality_caveats"] is non-empty list.


NARR-03 — Agent Crash and Recovery
FIELD
SPECIFICATION
Company
COMP-057 — technology sector, GROWTH trajectory, $1.1M requested
Trigger
FraudDetectionAgent starts processing NARR-03 and crashes after the load_facts node (simulated in test by calling agent._simulate_crash_after_node("load_facts")).
Expected sequence
AgentSessionFailed event in the crashed session's stream with recoverable=True and last_successful_node="load_facts". A new FraudDetectionAgent instance starts. Its reconstruct_agent_context() reads the crashed session's stream and identifies load_facts completed. New session starts with context_source="prior_session_replay:{crashed_session_id}". Recovery resumes from cross_reference_registry node (skipping load_facts). No duplicate load_facts work.
Test assertions
Exactly ONE FraudScreeningCompleted in fraud stream. Second AgentSessionStarted.context_source starts with "prior_session_replay:". AgentSessionRecovered event present in new session stream. Zero duplicate AgentNodeExecuted events for "load_facts" across both sessions.


NARR-04 — Compliance Hard Block (Montana)
FIELD
SPECIFICATION
Company
The Montana company (jurisdiction="MT") — whichever COMP-ID the generator assigned
Trigger
ComplianceAgent evaluates rules sequentially. REG-003 fails (Montana excluded).
Expected sequence
ComplianceRulePassed for REG-001. ComplianceRulePassed for REG-002. ComplianceRuleFailed for REG-003 with is_hard_block=True. No further rule events — evaluation stops. ComplianceCheckCompleted with overall_verdict="BLOCKED". ApplicationDeclined on loan stream with adverse_action_notice_required=True.
Test assertions
compliance stream has exactly 3 events: 2 Passed + 1 Failed (REG-004 through REG-006 never evaluated). NO DecisionGenerated event ever appears in the loan stream. ApplicationDeclined.payload["decline_reasons"] contains a string matching "REG-003". ApplicationDeclined.payload["adverse_action_notice_required"] is True.


NARR-05 — Human Override (The Loan Officer Approves Against the Agent)
FIELD
SPECIFICATION
Company
COMP-068 — retail sector, 15-year bank customer, DECLINING revenue trajectory (−8% YoY), high leverage. Prior loan repaid on schedule.
Trigger
Full pipeline runs. DecisionOrchestrator recommends DECLINE (HIGH risk, low confidence). A human loan officer overrides.
Expected sequence
DecisionGenerated with recommendation="DECLINE" and confidence=0.82. HumanReviewRequested on loan stream. Human override: HumanReviewCompleted with override=True, reviewer_id="LO-Sarah-Chen", final_decision="APPROVE", override_reason="15-year customer, prior repayment history, collateral offered". ApplicationApproved with approved_amount_usd=750000 (less than $950K requested), conditions=["Monthly revenue reporting for 12 months", "Personal guarantee from CEO"].
Test assertions
DecisionGenerated.payload["recommendation"]=="DECLINE". HumanReviewCompleted.payload["override"]==True. HumanReviewCompleted.payload["reviewer_id"]=="LO-Sarah-Chen". ApplicationApproved.payload["approved_amount_usd"]==750000. ApplicationApproved.payload["conditions"] has len==2. This is the application used for the regulatory package demo.



  SECTION 8  ·  SUBMISSION REQUIREMENTS

submission/
├── README.md              # Install → seed → run. Under 1 page. Must work from scratch.
├── requirements.txt       # Pinned. pip install -r requirements.txt must succeed.
├── .env.example           # Template with all var names. No real keys.
├── pytest.ini             # asyncio_mode = auto
├── DOMAIN_NOTES.md        # 6 questions. Graded separately.
├── DESIGN.md              # 6 sections. Graded separately.
├── DATA_GENERATION.md     # Simulator rules, PDF variants, event counts, API costs per agent.
│
├── datagen/               # Complete data generator (provided — include as-is)
│
├── ledger/                # Your application package
│   ├── schema/events.py   # Canonical schema (include as-is)
│   ├── event_store.py     # Your implementation
│   ├── upcasters.py       # Your implementation
│   ├── domain/aggregates/loan_application.py  # Your implementation
│   ├── projections/       # Your implementation
│   ├── agents/            # All 5 agents
│   ├── registry/client.py # Your implementation
│   └── mcp_server.py      # Your implementation
│
├── tests/                 # Full test suite
├── scripts/
│   ├── run_pipeline.py    # Process one application through all agents
│   └── demo_narr05.py     # Required demo — must run in < 90 seconds
│
└── artifacts/             # Generated artifacts (commit these)
    ├── test_results.txt
    ├── narrative_test_results.txt
    ├── occ_collision_report.txt
    ├── projection_lag_report.txt
    ├── api_cost_report.txt
    └── regulatory_package_NARR05.json



The api_cost_report.txt Requirement
Every LLM call is tagged with agent_type and workflow_id via the Week 5 Sentinel CostAttributor. The api_cost_report.txt is its output — generated by running your full pipeline on all 29 seed applications plus the 5 narrative applications. Costs over $50 total signal inefficient prompt design.
REQUIRED FIELD
EXAMPLE VALUE
SIGNALS
Total API cost for all 34 applications
$22.40
Above $50 → prompts too long. Below $8 → suspicious (may not be calling real LLM).
Average cost per application (range)
avg $0.66, range $0.18–$1.40
High variance → some application types much more expensive. Identify them.
Cost by agent (all 5)
DocProc $2.10  Credit $8.80  Fraud $4.20  Compliance $0.00  Orchestrator $7.30
Compliance is $0.00 (no LLM calls in rule evaluation). Orchestrator is often second-heaviest.
Most expensive single call
APEX-0049 Credit Analysis: $0.82 (5,200 input tokens)
Usually caused by very long historical financial context or many quality caveats requiring long prompts.


DESIGN.md — The Six Required Sections
SECTION
MINIMUM CONTENT
WHAT IS GRADED
1. Data Boundary Decisions
For each of the 7 data types in Section 1: why it lives where it does. Specifically: why are compliance_flags in the Applicant Registry and not in the event store?
Depth of reasoning, not correctness. A wrong answer with good reasoning scores higher than a right answer with no reasoning.
2. Aggregate Boundary Justification
For each of the 6 aggregate types: why this stream boundary. Include one alternative you considered and why you rejected it. Include the OCC implication of your boundary choice.
Concurrency analysis. "I chose this boundary because agents can work concurrently without stepping on each other" is the right kind of answer.
3. Week 3 Integration Architecture
The exact contract between DocumentProcessingAgent and the Week 3 pipeline. What is passed in. What comes back. What happens if the pipeline fails partially (some fields None, some populated).
Specifically: how do ExtractionCompleted events handle partial extraction? How does CreditAnalysisAgent respond to data_quality_caveats?
4. LangGraph Prompt Design — CreditAnalysisAgent
What is in the system prompt. What is in the user message. What is in neither (and why). What you tried that you then changed — with the before/after prompt and the reason for the change.
The "what I tried and changed" section is the most important. It demonstrates iterative prompt engineering discipline. One iteration is minimum; three is good.
5. Agent Failure Modes and Recovery
For each agent: the failure mode (LLM timeout, non-parseable JSON response, OCC max-retries exceeded, registry query failure), how the system recovers, what events are produced. Must cover NARR-03 crash recovery in detail.
Completeness. "The LLM always returns valid JSON" is not an acceptable answer.
6. What I Would Do Differently
One architectural decision per week (two total) that you would change given another full week. Specific, with the tradeoff analysis.
Honesty and engineering judgment. The most senior signal in the document. Vague answers score 1.



  SECTION 9  ·  ASSESSMENT RUBRIC

Score 3: system works end-to-end on the happy path. Score 4: failure modes handled correctly; DESIGN.md shows genuine reasoning. Score 5: all 5 narrative scenarios pass; projections within SLO; real prompt engineering evidence; Phase 6 attempted.

CRITERION
1
2
3
4
5
Event Store + OCC
No working store
append() works; no concurrency control
OCC enforced; concurrent double-append test passes; load_stream() and load_all() work
All methods; outbox in same transaction; load test passes with 0 unresolved OCC collisions
Above + DESIGN.md justifies schema; retry strategy quantified from load generator data
Document Pipeline Integration
Week 3 not connected
Files processed; no ExtractionCompleted events
ExtractionCompleted with FinancialFacts; QualityAssessmentCompleted; PackageReadyForAnalysis triggers next agent
NARR-02 (missing EBITDA) handled gracefully; data_quality_caveats appear in credit decision
Above + ExtractionFailed handled; credit agent adjusts confidence for low-quality fields; all 4 PDF variants exercised
LangGraph Agent Quality
No LangGraph; or no real LLM calls
LLM called; output not validated by Pydantic; no AgentNodeExecuted events
All 5 agents: LLM called, Pydantic output validation, AgentNodeExecuted per node, correct next-agent trigger
DESIGN.md Section 4 shows prompt iteration evidence; confidence and rationale fields substantive; NARR-03 crash recovery
Above + cost report shows <$0.70/application avg; Gas Town crash recovery works for all 5 agents
Business Rules + Narratives
No domain logic
Some rules; no narrative tests
All 6 aggregate rules enforced; NARR-01 (OCC) and NARR-04 (compliance block) pass
All 5 narrative tests pass
All 5 pass + load test: 0 unresolved OCC collisions; NARR-05 regulatory package independently verifiable
Projections + Daemon
No projections
One projection; no lag metric; no checkpointing
All 3 projections; daemon with checkpointing; lag metric exposed
SLO met under load (<800ms); temporal query on ComplianceAuditView; rebuild-from-zero tested
Above + projection_lag_report.txt artifact; rebuilds confirmed correct against seed events
MCP Server
No MCP server
Tools callable; no structured errors; no resources
All 8 tools + 6 resources; full lifecycle integration test (12 assertions) passes
Resources read only from projections; structured error types; MCP cost attribution working
Above + api_cost_report shows MCP tool cost breakdown correctly attributed
Data Architecture Quality
Generator fails or skips
Seed events present; no registry; agents use hardcoded data
Generator clean; registry seeded; agents query registry read-only; DATA_GENERATION.md present
All PDF variants exercised; event count verified; simulator-vs-real event shape compared in DATA_GENERATION.md
Above + 34+ applications processed through full pipeline; event store has >3,000 events; cost report complete
DESIGN.md Depth
Not present
Describes what was built (no reasoning)
All 6 sections present with basic reasoning
Aggregate boundary justification includes OCC analysis; LLM section shows at least one prompt iteration
DESIGN.md useful to a new engineer joining 6 months later; "what I would do differently" is honest and specific


Phase 6 Bonus — Score 5 Qualifier
Attempt only after all 5 narrative scenarios pass and DESIGN.md is complete. Without Phase 6, maximum score is 4 on any criterion.
DELIVERABLE
WHAT IT IS
GATE TEST
ARTIFACT
WhatIfProjector
Replays NARR-05 event history with a substituted credit decision (MEDIUM risk instead of HIGH risk). Filters causally dependent events. Shows whether the orchestrator would have approved without the human override.
python scripts/run_whatif.py --application APEX-NARR05 --substitute-credit-tier MEDIUM→ Different recommendation than real timeline. Causal filter verified by test.
artifacts/counterfactual_narr05.json
generate_regulatory_package()
Produces a self-contained JSON package for NARR-05: all events in order, all projection states at examination_date, audit chain integrity proof, model version provenance, plain-English narrative suitable for a bank regulator.
python tests/phase6/verify_package.py artifacts/regulatory_package_NARR05.json→ Hash chain valid. All events present. Package independently verifiable without accessing the live event store.
artifacts/regulatory_package_NARR05.json





TRP1 FDE Program  ·  Week 5: The Ledger v3  ·  March 2026  ·  Confidential
