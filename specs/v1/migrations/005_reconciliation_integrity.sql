-- Agent-Pay V1 reconciliation integrity
-- Apply after 004_control_binding.sql.

ALTER TABLE provider_events
    ADD COLUMN IF NOT EXISTS provider_operation_id UUID REFERENCES provider_operations(id);

CREATE INDEX IF NOT EXISTS ix_provider_events_operation
    ON provider_events(provider_operation_id, received_at DESC);

ALTER TABLE reconciliation_records
    ADD COLUMN IF NOT EXISTS checked_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS ix_reconciliation_status_created
    ON reconciliation_records(status, created_at DESC);

-- Provider event processing must be explicit; receipt alone never changes financial truth.
