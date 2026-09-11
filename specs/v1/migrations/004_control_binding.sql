-- Agent-Pay V1: bind financial-control selections to the payment intent.
-- Apply after 003_execution_integrity.sql.

ALTER TABLE payment_requests
    ADD COLUMN IF NOT EXISTS budget_id UUID REFERENCES budgets(id);

CREATE INDEX IF NOT EXISTS ix_payment_requests_budget ON payment_requests(budget_id);

-- budget_id is the intended budget selected for this payment request. The actual
-- reservation remains a separate row and is created only when execution is allowed.
