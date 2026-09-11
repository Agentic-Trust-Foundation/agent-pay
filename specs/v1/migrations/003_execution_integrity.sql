-- Agent-Pay V1 execution integrity convergence.
-- Apply after 001_stage4_convergence.sql and 002_ledger_accounts.sql.

-- Reusing an idempotency key for materially different intent is forbidden.
ALTER TABLE payment_requests
    ADD COLUMN IF NOT EXISTS request_fingerprint TEXT;

CREATE INDEX IF NOT EXISTS ix_payment_requests_account_fingerprint
    ON payment_requests(account_id, request_fingerprint);

-- Approval is an auditable decision history, not a one-row-per-request singleton.
-- Multiple approval attempts may exist; application logic binds the active decision
-- to the exact payment intent/version.
ALTER TABLE approvals
    DROP CONSTRAINT IF EXISTS approvals_payment_request_id_key;

CREATE INDEX IF NOT EXISTS ix_approvals_payment_request_created
    ON approvals(payment_request_id, requested_at DESC);

-- Provider operation records are append-oriented by operation identity.
CREATE INDEX IF NOT EXISTS ix_provider_operations_payment_created
    ON provider_operations(payment_id, created_at DESC);

-- Payment authentication is also a history, allowing step-up/retry attempts.
CREATE INDEX IF NOT EXISTS ix_payment_authentications_payment_created
    ON payment_authentications(payment_id, created_at DESC);
