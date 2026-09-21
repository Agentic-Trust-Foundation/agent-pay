-- Agent-Pay Phase 12: provider-operation race and worker recovery hardening.
-- Apply after 013_request_fingerprint.sql.

ALTER TABLE provider_operations
    ADD COLUMN IF NOT EXISTS processing_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS attempts INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_error TEXT;

CREATE INDEX IF NOT EXISTS ix_provider_operations_processing_recovery
    ON provider_operations(status, processing_at)
    WHERE status = 'PROCESSING';

-- Provider-operation status transitions are enforced by application compare-and-set
-- updates so webhook and worker finalization cannot overwrite each other's terminal outcome.
