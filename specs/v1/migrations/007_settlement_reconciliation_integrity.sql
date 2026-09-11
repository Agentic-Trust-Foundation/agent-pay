-- Agent-Pay V1 settlement/reconciliation workflow integrity.
-- Apply after 006_payment_lifecycle.sql.

-- A settlement report is reconciled at most once. Reprocessing the same
-- provider settlement reference must be a no-op.
CREATE UNIQUE INDEX IF NOT EXISTS ux_reconciliation_settlement
    ON reconciliation_records(settlement_id)
    WHERE settlement_id IS NOT NULL;

-- A provider operation may be reconciled at most once in V1. This keeps
-- reconciliation append-oriented and prevents duplicate financial conclusions.
CREATE UNIQUE INDEX IF NOT EXISTS ux_reconciliation_provider_operation
    ON reconciliation_records(provider_operation_id)
    WHERE provider_operation_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_settlements_status_created
    ON settlements(status, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_provider_operations_reference
    ON provider_operations(provider_reference, created_at DESC)
    WHERE provider_reference IS NOT NULL;

-- Reconciliation is observational in V1: a discrepancy never changes the
-- ledger automatically. Investigation/resolution is an explicit later action.
