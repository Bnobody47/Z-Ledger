# Project Scope — Reconciling the Documentation

Your `doc file.md` contains **three major sections** that together define the full project. This document summarizes what's in there and how it maps to our scaffold.

---

## What's in doc file.md

### 1. Original Week 5 PDF Spec (Phases 0–6)

The first part matches the Week 5 PDF exactly:

- **4 aggregates**: LoanApplication, AgentSession, ComplianceRecord, AuditLedger
- **Event catalogue**: ~15 event types (ApplicationSubmitted, CreditAnalysisCompleted, etc.)
- **Phases**: 0 (DOMAIN_NOTES) → 1 (Event Store) → 2 (Aggregates) → 3 (Projections) → 4 (Upcasting, Integrity, Gas Town) → 5 (MCP) → 6 (Bonus: What-If, Regulatory Package)
- **Stack**: PostgreSQL + psycopg3/asyncpg, Python
- **Deliverables**: schema.sql, event_store.py, aggregates, projections, MCP tools/resources, tests

**Our scaffold follows this spec.**

---

### 2. Extended "Agentic Document-to-Decision Platform" (Two-Week Version)

A more detailed spec appears later in the doc, describing a **two-week** build with:

| Component | Extended Spec |
|-----------|----------------|
| **Aggregates** | 7 stream types: `loan-*`, `docpkg-*`, `agent-*`, `credit-*`, `fraud-*`, `compliance-*`, `audit-*` |
| **Event types** | 45 events in `ledger/schema/events.py` (canonical schema) |
| **Agents** | 5 LangGraph agents: DocumentProcessingAgent, CreditAnalysisAgent, FraudDetectionAgent, ComplianceAgent, DecisionOrchestratorAgent |
| **Data generator** | `datagen/generate_all.py` — 80 companies, 160 PDFs, 80 Excel, 80 CSV, 1,847 seed events |
| **Applicant Registry** | External read-only PostgreSQL schema `applicant_registry.*` |
| **Narrative scenarios** | NARR-01 (OCC), NARR-02 (missing EBITDA), NARR-03 (crash recovery), NARR-04 (compliance block), NARR-05 (regulatory package) |
| **MCP** | **fastmcp** (>=0.9) — decorator-based `@mcp.tool()`, `@mcp.resource()` |
| **Folder layout** | `apex-ledger/` with `datagen/`, `ledger/`, `documents/`, `tests/`, `scripts/`, `artifacts/` |

**Differences from original Week 5:**

- `credit-{id}` and `fraud-{id}` are **separate aggregates** (CreditRecord, FraudScreening), not just events on the loan stream
- `docpkg-{id}` (DocumentPackage) — document extraction lifecycle
- AgentSession uses `AgentSessionStarted` (not `AgentContextLoaded`) and includes `AgentNodeExecuted` per LangGraph node
- Data generator is mandatory — run first, everything depends on it
- Week 3 pipeline (MinerU/Docling) plugs into DocumentProcessingAgent

---

### 3. Event Sourcing Practitioner Manual

Reference material covering:

- **Part I**: Conceptual map (ES vs EDA, CQRS, DDD, Outbox, etc.)
- **Part II**: Glossary (Event Store, Stream, Aggregate, OCC, Snapshot, Projection, etc.)
- **Part IV**: Event payload schema patterns (identity events, decision events with causal chain, compensating events)
- **Part V**: Query patterns (load stream, optimistic append, projection daemon polling) with SQL
- **Part VI**: Solution architectures

Use this as implementation guidance, not as a change to the spec.

---

## How to Proceed

### Option A: Original Week 5 Only (Current Scaffold)

Stick with the **4-aggregate** spec from the PDF. Our scaffold matches this. No data generator, no LangGraph agents — just the event store, aggregates, projections, upcasting, integrity, Gas Town, and MCP.

**Use when**: You want to complete the core Week 5 challenge first.

---

### Option B: Full Extended Platform

Adopt the **7-aggregate** spec with data generator and 5 LangGraph agents. This implies:

1. Add `datagen/` and run `generate_all.py` first
2. Add `credit-*` and `fraud-*` aggregates
3. Add `docpkg-*` (DocumentPackage) aggregate
4. Implement 5 LangGraph agents
5. Use **fastmcp** for MCP
6. Integrate Week 3 extraction pipeline
7. Add narrative tests (NARR-01 through NARR-05)

**Use when**: You are doing the full two-week program.

---

### Option C: Hybrid (Recommended)

1. **Phase 1–5**: Implement the original Week 5 spec (our scaffold) — event store, 4 aggregates, projections, MCP.
2. **Phase 6+**: Extend with data generator, extra aggregates (`credit`, `fraud`, `docpkg`), and LangGraph agents as a second phase.

---

## Technology Stack (from doc file)

| Component | Package | Version |
|-----------|---------|---------|
| Event store DB | asyncpg | >=0.29 |
| Schemas | pydantic | >=2.6 |
| MCP server | **fastmcp** | >=0.9 |
| Agent graphs | langgraph | >=0.2 |
| LLM API | anthropic | >=0.30 |
| PDF generation | reportlab | >=4.2 |
| Excel | openpyxl | >=3.1 |
| Testing | pytest + pytest-asyncio | >=8.0, >=0.23 |

---

## Next Steps

1. **Confirm scope**: Original Week 5 (A), full platform (B), or hybrid (C).
2. **Fill DOMAIN_NOTES.md** before implementation (Phase 0).
3. **Implement Phase 1** (Event Store + concurrency test) next.
