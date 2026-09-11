-- Agent-Pay V1 reconciliation semantics for multiple settlement reports.
-- Apply after 007_settlement_reconciliation_integrity.sql.

-- Multiple settlement/reconciliation reports may legitimately refer to the
-- same provider operation (for example a corrected or discrepant report).
-- Deduplication is by settlement identity, not by provider operation.
DROP INDEX IF EXISTS ux_reconciliation_provider_operation;

-- The settlement identity remains the idempotency boundary.
CREATE UNIQUE INDEX IF NOT EXISTS ux_reconciliation_settlement
    ON reconciliation_records(settlement_id)
    WHERE settlement_id IS NOT NULL;

-- A discrepancy is observational: recording it must never mutate payment,
-- budget, or ledger truth automatically.
