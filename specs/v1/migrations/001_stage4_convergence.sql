-- Agent-Pay V1 Stage 4 persistence convergence
-- Apply after specs/v1/database-schema.sql.

ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'AUTHENTICATION_REQUIRED';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'AUTHENTICATED';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'UNKNOWN_EXTERNAL_OUTCOME';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'REFUND_PROCESSING';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'REFUND_FAILED';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'VOID_REQUESTED';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'VOIDED';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'VOID_FAILED';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'SETTLEMENT_PENDING';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'SETTLED';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'SETTLEMENT_FAILED';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'DISPUTED';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'CHARGEBACK';

CREATE TABLE IF NOT EXISTS authorization_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    agent_id UUID NOT NULL REFERENCES agents(id),
    delegation_id UUID REFERENCES delegations(id),
    payment_request_id UUID REFERENCES payment_requests(id),
    issuer_reference TEXT,
    evidence_type TEXT NOT NULL,
    subject_reference TEXT NOT NULL,
    audience TEXT,
    issued_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    evidence JSONB NOT NULL,
    verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS policy_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID NOT NULL REFERENCES policies(id),
    version INTEGER NOT NULL,
    rules JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (policy_id, version)
);

CREATE TABLE IF NOT EXISTS budget_reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    budget_id UUID NOT NULL REFERENCES budgets(id),
    payment_request_id UUID NOT NULL REFERENCES payment_requests(id),
    amount NUMERIC(20,4) NOT NULL,
    currency CHAR(3) NOT NULL,
    status TEXT NOT NULL DEFAULT 'RESERVED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    released_at TIMESTAMPTZ,
    consumed_at TIMESTAMPTZ,
    CHECK (amount > 0),
    UNIQUE (budget_id, payment_request_id)
);

CREATE TABLE IF NOT EXISTS payment_authentications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES payments(id),
    method TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'REQUIRED',
    provider_reference TEXT,
    challenge_reference TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS provider_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES payments(id),
    operation_type TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    provider_reference TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING',
    request_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    response_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    UNIQUE (idempotency_key)
);

CREATE TABLE IF NOT EXISTS provider_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name TEXT NOT NULL,
    provider_event_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    signature_valid BOOLEAN NOT NULL DEFAULT FALSE,
    payload JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at TIMESTAMPTZ,
    processing_status TEXT NOT NULL DEFAULT 'RECEIVED',
    UNIQUE (provider_name, provider_event_id)
);

CREATE TABLE IF NOT EXISTS settlements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name TEXT NOT NULL,
    settlement_reference TEXT NOT NULL,
    currency CHAR(3) NOT NULL,
    amount NUMERIC(20,4) NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    reported_at TIMESTAMPTZ,
    settled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (provider_name, settlement_reference)
);

CREATE TABLE IF NOT EXISTS reconciliation_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    settlement_id UUID REFERENCES settlements(id),
    provider_operation_id UUID REFERENCES provider_operations(id),
    status TEXT NOT NULL DEFAULT 'PENDING',
    expected_amount NUMERIC(20,4),
    observed_amount NUMERIC(20,4),
    expected_currency CHAR(3),
    observed_currency CHAR(3),
    discrepancy_code TEXT,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS outbox_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    aggregate_type TEXT NOT NULL,
    aggregate_id UUID NOT NULL,
    payload JSONB NOT NULL,
    correlation_id TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING',
    attempts INTEGER NOT NULL DEFAULT 0,
    available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ledger_journals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    currency CHAR(3) NOT NULL,
    reference_type TEXT NOT NULL,
    reference_id UUID,
    idempotency_key TEXT NOT NULL UNIQUE,
    correlation_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ledger_postings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_id UUID NOT NULL REFERENCES ledger_journals(id) ON DELETE CASCADE,
    ledger_account_id UUID NOT NULL REFERENCES ledger_accounts(id),
    side TEXT NOT NULL CHECK (side IN ('DEBIT', 'CREDIT')),
    amount NUMERIC(20,4) NOT NULL CHECK (amount > 0),
    currency CHAR(3) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE payment_requests ADD COLUMN IF NOT EXISTS policy_version_id UUID REFERENCES policy_versions(id);
ALTER TABLE payment_requests ADD COLUMN IF NOT EXISTS budget_reservation_id UUID REFERENCES budget_reservations(id);
ALTER TABLE payment_requests ADD COLUMN IF NOT EXISTS authorization_evidence_id UUID REFERENCES authorization_evidence(id);
ALTER TABLE payments ADD COLUMN IF NOT EXISTS provider_operation_id UUID REFERENCES provider_operations(id);
ALTER TABLE payments ADD COLUMN IF NOT EXISTS authorization_context_hash TEXT;

CREATE INDEX IF NOT EXISTS ix_authorization_evidence_payment ON authorization_evidence(payment_request_id);
CREATE INDEX IF NOT EXISTS ix_budget_reservations_payment ON budget_reservations(payment_request_id);
CREATE INDEX IF NOT EXISTS ix_provider_operations_payment ON provider_operations(payment_id);
CREATE INDEX IF NOT EXISTS ix_provider_events_status_received ON provider_events(processing_status, received_at);
CREATE INDEX IF NOT EXISTS ix_outbox_pending ON outbox_events(status, available_at, created_at);
CREATE INDEX IF NOT EXISTS ix_ledger_postings_journal ON ledger_postings(journal_id);

-- The legacy ledger_entries table remains for backward compatibility. New financial
-- mutations should converge on ledger_journals + ledger_postings as the authoritative
-- double-entry model.
