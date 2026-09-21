-- Track the start of an outbox claim so abandoned PROCESSING rows can be
-- recovered by recover_stale(). Safe to apply to databases where the column
-- already exists.
ALTER TABLE outbox_events
    ADD COLUMN IF NOT EXISTS processing_at TIMESTAMPTZ;

-- Existing PROCESSING rows predate lease tracking. Make them immediately
-- eligible for recovery rather than leaving them permanently unclaimable.
UPDATE outbox_events
SET processing_at = COALESCE(processing_at, created_at)
WHERE status = 'PROCESSING';
