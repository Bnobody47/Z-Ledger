-- Z Ledger: PostgreSQL setup script
-- Run as postgres superuser. If user/DB exist, ignore those errors.
-- Example: "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -f scripts/setup_db.sql

CREATE USER bnobody WITH PASSWORD 'beahhal';
CREATE DATABASE z_ledger OWNER bnobody;
GRANT ALL PRIVILEGES ON DATABASE z_ledger TO bnobody;

\c z_ledger

GRANT ALL ON SCHEMA public TO bnobody;

-- Apply event store schema (run from project root so \i finds src/schema.sql)
\i src/schema.sql

GRANT ALL ON ALL TABLES IN SCHEMA public TO bnobody;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO bnobody;
