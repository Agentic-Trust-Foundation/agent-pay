-- Agent-Pay V1 capture / void / refund lifecycle integrity.
-- Apply after 005_reconciliation_integrity.sql.

-- Transaction history must be independently idempotent and append-oriented.
ALTER TABLE transactions
    ADD COLUMN IF NOT EXISTS idempotency_key TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS ux_transactions_idempotency
    ON transactions(idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_transactions_payment_type_created
    ON transactions(payment_id, type, created_at DESC);

-- Capture/void/refund are provider operations, not alternate payment identities.
CREATE INDEX IF NOT EXISTS ix_provider_operations_payment_type
    ON provider_operations(payment_id, operation_type, created_at DESC);

-- Refunds must point to the original posted transaction when applicable.
CREATE INDEX IF NOT EXISTS ix_transactions_original
    ON transactions(original_transaction_id);

-- Keep the payment lifecycle explicit. REFUND_PROCESSING/REFUNDED and
-- VOID_REQUESTED/VOIDED are already introduced by migration 001.
-- Disputes/chargebacks remain separate future lifecycle outcomes.
