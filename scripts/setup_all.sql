-- Z Ledger: Full setup (user + DB + schema) in one file
-- Run as postgres: psql -U postgres -f scripts/setup_all.sql
-- If user/DB exist, ignore those errors.

CREATE USER bnobody WITH PASSWORD 'beahhal';
CREATE DATABASE z_ledger OWNER bnobody;
GRANT ALL PRIVILEGES ON DATABASE z_ledger TO bnobody;

\c z_ledger

GRANT ALL ON SCHEMA public TO bnobody;

-- Event store schema
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS events (
  event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  stream_id TEXT NOT NULL,
  stream_position BIGINT NOT NULL,
  global_position BIGINT GENERATED ALWAYS AS IDENTITY,
  event_type TEXT NOT NULL,
  event_version SMALLINT NOT NULL DEFAULT 1,
  payload JSONB NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
  CONSTRAINT uq_stream_position UNIQUE (stream_id, stream_position)
);

CREATE INDEX IF NOT EXISTS idx_events_stream_id ON events (stream_id, stream_position);
CREATE INDEX IF NOT EXISTS idx_events_global_pos ON events (global_position);
CREATE INDEX IF NOT EXISTS idx_events_type ON events (event_type);
CREATE INDEX IF NOT EXISTS idx_events_recorded ON events (recorded_at);

CREATE TABLE IF NOT EXISTS event_streams (
  stream_id TEXT PRIMARY KEY,
  aggregate_type TEXT NOT NULL,
  current_version BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  archived_at TIMESTAMPTZ,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS projection_checkpoints (
  projection_name TEXT PRIMARY KEY,
  last_position BIGINT NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS outbox (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id UUID NOT NULL REFERENCES events(event_id),
  destination TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  published_at TIMESTAMPTZ,
  attempts SMALLINT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_outbox_unpublished ON outbox (created_at) WHERE published_at IS NULL;

CREATE TABLE IF NOT EXISTS projection_application_summary (
  application_id TEXT PRIMARY KEY,
  state TEXT,
  applicant_id TEXT,
  requested_amount_usd DOUBLE PRECISION,
  approved_amount_usd DOUBLE PRECISION,
  risk_tier TEXT,
  fraud_score DOUBLE PRECISION,
  compliance_status TEXT,
  decision TEXT,
  agent_sessions_completed TEXT[] NOT NULL DEFAULT '{}',
  last_event_type TEXT,
  last_event_at TIMESTAMPTZ,
  human_reviewer_id TEXT,
  final_decision_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS projection_agent_performance (
  agent_id TEXT NOT NULL,
  model_version TEXT NOT NULL,
  analyses_completed BIGINT NOT NULL DEFAULT 0,
  decisions_generated BIGINT NOT NULL DEFAULT 0,
  avg_confidence_score DOUBLE PRECISION,
  avg_duration_ms DOUBLE PRECISION,
  approve_rate DOUBLE PRECISION NOT NULL DEFAULT 0,
  decline_rate DOUBLE PRECISION NOT NULL DEFAULT 0,
  refer_rate DOUBLE PRECISION NOT NULL DEFAULT 0,
  human_override_rate DOUBLE PRECISION NOT NULL DEFAULT 0,
  first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (agent_id, model_version)
);

CREATE TABLE IF NOT EXISTS projection_compliance_audit (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  application_id TEXT NOT NULL,
  as_of TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  compliance_status TEXT NOT NULL DEFAULT 'UNKNOWN',
  checks JSONB NOT NULL DEFAULT '[]'::jsonb,
  regulation_versions JSONB NOT NULL DEFAULT '{}'::jsonb,
  last_event_type TEXT,
  last_event_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_projection_compliance_audit_lookup ON projection_compliance_audit (application_id, as_of DESC);

-- Applicant Registry (optional — for LLM agents)
CREATE SCHEMA IF NOT EXISTS applicant_registry;
CREATE TABLE IF NOT EXISTS applicant_registry.companies (
    company_id TEXT PRIMARY KEY, name TEXT NOT NULL, industry TEXT NOT NULL,
    naics TEXT NOT NULL, jurisdiction TEXT NOT NULL, legal_type TEXT NOT NULL,
    founded_year INT NOT NULL, employee_count INT NOT NULL, ein TEXT UNIQUE,
    address_city TEXT NOT NULL, address_state TEXT NOT NULL,
    relationship_start DATE NOT NULL, account_manager TEXT NOT NULL,
    risk_segment TEXT NOT NULL CHECK (risk_segment IN ('LOW','MEDIUM','HIGH')),
    trajectory TEXT NOT NULL, submission_channel TEXT NOT NULL, ip_region TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS applicant_registry.financial_history (
    id SERIAL PRIMARY KEY, company_id TEXT NOT NULL REFERENCES applicant_registry.companies(company_id),
    fiscal_year INT NOT NULL, total_revenue NUMERIC(15,2) NOT NULL, gross_profit NUMERIC(15,2) NOT NULL,
    operating_expenses NUMERIC(15,2) NOT NULL, operating_income NUMERIC(15,2) NOT NULL,
    ebitda NUMERIC(15,2) NOT NULL, depreciation_amortization NUMERIC(15,2) NOT NULL DEFAULT 0,
    interest_expense NUMERIC(15,2) NOT NULL DEFAULT 0, income_before_tax NUMERIC(15,2) NOT NULL DEFAULT 0,
    tax_expense NUMERIC(15,2) NOT NULL DEFAULT 0, net_income NUMERIC(15,2) NOT NULL,
    total_assets NUMERIC(15,2) NOT NULL, current_assets NUMERIC(15,2) NOT NULL DEFAULT 0,
    cash_and_equivalents NUMERIC(15,2) NOT NULL, accounts_receivable NUMERIC(15,2) NOT NULL DEFAULT 0,
    inventory NUMERIC(15,2) NOT NULL DEFAULT 0, total_liabilities NUMERIC(15,2) NOT NULL,
    current_liabilities NUMERIC(15,2) NOT NULL DEFAULT 0, long_term_debt NUMERIC(15,2) NOT NULL,
    total_equity NUMERIC(15,2) NOT NULL, operating_cash_flow NUMERIC(15,2) NOT NULL DEFAULT 0,
    investing_cash_flow NUMERIC(15,2) NOT NULL DEFAULT 0, financing_cash_flow NUMERIC(15,2) NOT NULL DEFAULT 0,
    free_cash_flow NUMERIC(15,2) NOT NULL DEFAULT 0, debt_to_equity NUMERIC(8,4),
    current_ratio NUMERIC(8,4), debt_to_ebitda NUMERIC(8,4), interest_coverage_ratio NUMERIC(8,4),
    gross_margin NUMERIC(8,4), ebitda_margin NUMERIC(8,4), net_margin NUMERIC(8,4),
    balance_sheet_check BOOLEAN NOT NULL DEFAULT TRUE, UNIQUE (company_id, fiscal_year)
);
CREATE TABLE IF NOT EXISTS applicant_registry.compliance_flags (
    id SERIAL PRIMARY KEY, company_id TEXT NOT NULL REFERENCES applicant_registry.companies(company_id),
    flag_type TEXT NOT NULL CHECK (flag_type IN ('AML_WATCH','SANCTIONS_REVIEW','PEP_LINK')),
    severity TEXT NOT NULL CHECK (severity IN ('LOW','MEDIUM','HIGH')),
    is_active BOOLEAN NOT NULL, added_date DATE NOT NULL, note TEXT
);
CREATE TABLE IF NOT EXISTS applicant_registry.loan_relationships (
    id SERIAL PRIMARY KEY, company_id TEXT NOT NULL REFERENCES applicant_registry.companies(company_id),
    loan_amount NUMERIC(15,2) NOT NULL, loan_year INT NOT NULL,
    was_repaid BOOLEAN NOT NULL, default_occurred BOOLEAN NOT NULL, note TEXT
);
GRANT USAGE ON SCHEMA applicant_registry TO bnobody;
GRANT ALL ON ALL TABLES IN SCHEMA applicant_registry TO bnobody;

-- Transfer ownership so bnobody can TRUNCATE in tests
ALTER TABLE events OWNER TO bnobody;
ALTER TABLE event_streams OWNER TO bnobody;
ALTER TABLE projection_checkpoints OWNER TO bnobody;
ALTER TABLE outbox OWNER TO bnobody;
ALTER TABLE projection_application_summary OWNER TO bnobody;
ALTER TABLE projection_agent_performance OWNER TO bnobody;
ALTER TABLE projection_compliance_audit OWNER TO bnobody;
ALTER SEQUENCE events_global_position_seq OWNER TO bnobody;
ALTER SEQUENCE projection_compliance_audit_id_seq OWNER TO bnobody;

GRANT ALL ON ALL TABLES IN SCHEMA public TO bnobody;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO bnobody;
