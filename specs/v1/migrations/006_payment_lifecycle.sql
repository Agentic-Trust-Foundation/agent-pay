-- Agent-Pay V1 capture / void / refund lifecycle integrity.
-- Apply after 005_reconciliation_integrity.sql.

ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'AUTHORIZED';

-- Transaction history must be independently idempotent and append-oriented.
ALTER TABLE transactions
    ADD COLUMN IF NOT EXISTS idempotency_key TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS ux_transactions_idempotency
    ON transactions(idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_transactions_payment_type_created
    ON transactions(payment_id, type, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_provider_operations_payment_type
    ON provider_operations(payment_id, operation_type, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_transactions_original
    ON transactions(original_transaction_id);

-- Payment states distinguish an external authorization from a captured payment.
-- REFUND_PROCESSING/REFUNDED and VOID_REQUESTED/VOIDED are defined by migration 001.
-- Disputes/chargebacks remain separate future lifecycle outcomes.
