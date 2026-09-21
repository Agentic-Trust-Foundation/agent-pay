-- Agent-Pay Phase 2: durable outbox worker recovery metadata.
-- Keeps publication outside DB transactions while making abandoned claims recoverable.

ALTER TABLE outbox_events
    ADD COLUMN IF NOT EXISTS processing_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS ix_outbox_processing_recovery
    ON outbox_events(status, processing_at)
    WHERE status = 'PROCESSING';

ALTER TABLE outbox_events
    DROP CONSTRAINT IF EXISTS outbox_events_status_ck;

ALTER TABLE outbox_events
    ADD CONSTRAINT outbox_events_status_ck
    CHECK (status IN ('PENDING','PROCESSING','PUBLISHED','DEAD_LETTER'));
