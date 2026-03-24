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

### Documentation
- **`doc file.md`** — Full project documentation (Week 5 PDF + extended Agentic Document-to-Decision spec + Event Sourcing Practitioner Manual). See `docs/PROJECT_SCOPE.md` for a reconciled summary and scope options.

### Next steps
1. **Confirm scope** — Original Week 5 (4 aggregates) vs extended platform (7 aggregates, data generator, LangGraph agents). See `docs/PROJECT_SCOPE.md`.
2. **Fill `DOMAIN_NOTES.md`** — Answer the 6 questions before implementation (Phase 0).
3. **Implement Phase 1** — Event store core with PostgreSQL, optimistic concurrency, and the double-decision test.

### Quick start (later)
Once code is implemented, this README will include:
- Database provisioning and migration steps
- How to run the daemon and MCP server
- How to run the full test suite

### Database setup (one-time)
```powershell
.\scripts\run_setup.ps1
```
You'll be prompted for the postgres superuser password. This creates user `bnobody`, password `beahhal`, and database `z_ledger`.

### Interim testing (now)
1. Install dependencies:
   - `python -m pip install -e ".[dev]"`
2. Set DB connection (PowerShell):
   - `$env:DATABASE_URL="postgresql://bnobody:beahhal@localhost:5432/z_ledger"`
3. Run interim test:
   - `python -m pytest tests/test_concurrency.py -v -s`
4. Run all currently scaffolded tests:
   - `python -m pytest -q`

Notes:
- If `DATABASE_URL` is not set, DB integration tests are skipped by design.
- `tests/test_concurrency.py` auto-applies `src/schema.sql` and truncates event tables before running.

### LLM agents (credit analysis)
From the Apex Ledger starter:
1. Copy `.env.example` to `.env` and add your `ANTHROPIC_API_KEY`.
2. Re-run setup to create `applicant_registry` schema: `psql -U postgres -f scripts/setup_all.sql`
3. Seed registry (optional): `python scripts/seed_registry.py`
4. Run credit analysis: `python scripts/run_pipeline.py --application app-1`

### Final submission testing checklist
1. Start PostgreSQL and create DB:
   - `createdb z_ledger` (or create manually)
2. Set environment variable:
   - `$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/z_ledger"`
3. Install deps:
   - `python -m pip install -e ".[dev]"`
4. Run all required tests:
   - `python -m pytest tests/test_concurrency.py -q`
   - `python -m pytest tests/test_upcasting.py -q`
   - `python -m pytest tests/test_projections.py -q`
   - `python -m pytest tests/test_gas_town.py -q`
   - `python -m pytest tests/test_mcp_lifecycle.py -q`
   - `python -m pytest -q`
5. Optional quality check:
   - `python -m ruff check src tests`

If any test is reported as skipped, confirm `DATABASE_URL` is exported in the same shell session running `pytest`.

