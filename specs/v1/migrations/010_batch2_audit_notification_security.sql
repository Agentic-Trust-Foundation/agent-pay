-- Agent-Pay V1 Batch 2: audit/notification idempotency and security invariants.
-- Apply after 009_payment_instrument_integrity.sql.

ALTER TABLE audit_events
    ADD COLUMN IF NOT EXISTS event_id UUID,
    ADD COLUMN IF NOT EXISTS immutable_digest TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS ux_audit_events_event_id
    ON audit_events(event_id)
    WHERE event_id IS NOT NULL;

ALTER TABLE notifications
    ADD COLUMN IF NOT EXISTS source_event_id UUID,
    ADD COLUMN IF NOT EXISTS attempts INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS last_error TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS ux_notifications_source_event
    ON notifications(source_event_id)
    WHERE source_event_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_notifications_delivery
    ON notifications(status, available_at, created_at);

ALTER TABLE outbox_events
    ADD COLUMN IF NOT EXISTS last_error TEXT;

ALTER TABLE provider_events
    ADD COLUMN IF NOT EXISTS payload_digest TEXT;

CREATE OR REPLACE FUNCTION reject_audit_mutation() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit_events are append-only';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_events_immutable ON audit_events;
CREATE TRIGGER trg_audit_events_immutable
BEFORE UPDATE OR DELETE ON audit_events
FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation();
