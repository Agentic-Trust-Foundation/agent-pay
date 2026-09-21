-- Agent-Pay Phase 6: durable request fingerprint for idempotency collision detection.

ALTER TABLE payment_requests
    ADD COLUMN IF NOT EXISTS request_fingerprint TEXT;

CREATE INDEX IF NOT EXISTS ix_payment_requests_idempotency_lookup
    ON payment_requests(account_id, idempotency_key);

-- The application compares the fingerprint on an existing idempotency key.
-- The unique business key remains (account_id, idempotency_key); the fingerprint
-- is evidence used to reject reuse of that key for a different request.
