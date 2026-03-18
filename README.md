## Z Ledger — TRP1 Week 5 “The Ledger”

This workspace is a scaffold for **TRP1 Week 5: Agentic Event Store & Enterprise Audit Infrastructure** (“The Ledger”).

### What we’re building
- **An append-only event store (PostgreSQL)** that is the *source of truth* for multi-agent decisions and audit history.
- **Domain aggregates + command handlers (CQRS write side)** that enforce business rules by appending events with **optimistic concurrency**.
- **Async projections + projection daemon (CQRS read side)** that build fast query models with **measured projection lag**.
- **Upcasting + cryptographic integrity** to handle schema evolution without mutating history, and to detect tampering.
- **An MCP server** that exposes:
  - **Tools = Commands** (write side)
  - **Resources = Queries** (read side)

### Repo layout (high level)
- `docs/` — `DOMAIN_NOTES.md` and `DESIGN.md` (graded alongside code)
- `src/` — schema, event store, aggregates, projections, MCP server
- `tests/` — concurrency, upcasting immutability, projection lag, Gas Town recovery, MCP lifecycle

### Quick start (later)
Once code is implemented, this README will include:
- Database provisioning and migration steps
- How to run the daemon and MCP server
- How to run the full test suite

