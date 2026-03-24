-- Fix ownership for bnobody (run as postgres after setup)
-- Use if tests fail with "must be owner of table events"

\c z_ledger

ALTER TABLE events OWNER TO bnobody;
ALTER TABLE event_streams OWNER TO bnobody;
ALTER TABLE projection_checkpoints OWNER TO bnobody;
ALTER TABLE outbox OWNER TO bnobody;
ALTER TABLE projection_application_summary OWNER TO bnobody;
ALTER TABLE projection_agent_performance OWNER TO bnobody;
ALTER TABLE projection_compliance_audit OWNER TO bnobody;
ALTER SEQUENCE events_global_position_seq OWNER TO bnobody;
ALTER SEQUENCE projection_compliance_audit_id_seq OWNER TO bnobody;
