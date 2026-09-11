-- Agent-Pay V1 Stage 3 convergence migration
-- Additive migration from the original implementation-oriented schema.
-- Apply after specs/v1/database-schema.sql.
-- Financial records remain append-oriented; do not rewrite historical entries.

-- 1. Expand payment lifecycle without renaming existing values.
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

-- 2. Authorization evidence: durable, operation-bindable provenance.
CREATE TABLE IF NOT EXISTS authorization_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    agent_id UUID REFERENCES agents(id),
    delegation_id UUID REFERENCES delegations(id),
    issuer TEXT,
    evidence_type TEXT NOT NULL,
    evidence_digest TEXT,
    source_reference TEXT,
    issued_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (expires_at IS NULL OR issued_at IS NULL OR expires_at > issued_at)
);

-- 3. Immutable policy versions.
CREATE TABLE IF NOT EXISTS policy_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID NOT NULL REFERENCES policies(id),
    version_number INTEGER NOT NULL,
    rules JSONB NOT NULL DEFAULT '{}'::jsonb,
    content_digest TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (policy_id, version_number)
);

-- 4. Budget reservations are distinct from wallet holds.
CREATE TYPE budget_reservation_status AS ENUM ('RESERVED', 'CONSUMED', 'RELEASED', 'EXPIRED', 'CANCELLED');

CREATE TABLE IF NOT EXISTS budget_reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    budget_id UUID NOT NULL REFERENCES budgets(id),
    payment_request_id UUID NOT NULL REFERENCES payment_requests(id),
    amount NUMERIC(20,4) NOT NULL,
    currency CHAR(3) NOT NULL,
    status budget_reservation_status NOT NULL DEFAULT 'RESERVED',
    idempotency_key TEXT NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (amount > 0),
    UNIQUE (budget_id, idempotency_key)
);

-- 5. Approval history: remove the old one-row-per-request limitation.
ALTER TABLE approvals DROP CONSTRAINT IF EXISTS approvals_payment_request_id_key;
ALTER TABLE approvals ADD COLUMN IF NOT EXISTS intent_digest TEXT;
ALTER TABLE approvals ADD COLUMN IF NOT EXISTS decided_at TIMESTAMPTZ;
ALTER TABLE approvals ADD COLUMN IF NOT EXISTS supersedes_approval_id UUID REFERENCES approvals(id);
CREATE INDEX IF NOT EXISTS ix_approvals_payment_request_created
    ON approvals(payment_request_id, requested_at DESC);

-- 6. Bind payment request to durable authorization and correlation context.
ALTER TABLE payment_requests ADD COLUMN IF NOT EXISTS authorization_evidence_id UUID REFERENCES authorization_evidence(id);
ALTER TABLE payment_requests ADD COLUMN IF NOT EXISTS policy_version_id UUID REFERENCES policy_versions(id);
ALTER TABLE payment_requests ADD COLUMN IF NOT EXISTS commerce_context JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE payment_requests ADD COLUMN IF NOT EXISTS correlation_id TEXT;
ALTER TABLE payment_requests ADD COLUMN IF NOT EXISTS request_fingerprint TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS ux_payment_request_idempotency_fingerprint
    ON payment_requests(account_id, idempotency_key, request_fingerprint)
    WHERE request_fingerprint IS NOT NULL;

-- 7. Payment authentication is persisted separately from approval.
CREATE TYPE payment_authentication_status AS ENUM ('NOT_REQUIRED', 'REQUIRED', 'PENDING', 'AUTHENTICATED', 'FAILED', 'EXPIRED');

CREATE TABLE IF NOT EXISTS payment_authentications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES payments(id),
    status payment_authentication_status NOT NULL DEFAULT 'REQUIRED',
    method TEXT,
    provider_reference TEXT,
    challenge_reference TEXT,
    expires_at TIMESTAMPTZ,
    authenticated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_payment_auth_payment ON payment_authentications(payment_id, created_at DESC);

-- 8. Provider operations make external execution explicitly idempotent.
CREATE TYPE provider_operation_status AS ENUM ('REQUESTED', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'UNKNOWN');

CREATE TABLE IF NOT EXISTS provider_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID REFERENCES payments(id),
    transaction_id UUID REFERENCES transactions(id),
    operation_type TEXT NOT NULL,
    status provider_operation_status NOT NULL DEFAULT 'REQUESTED',
    idempotency_key TEXT NOT NULL,
    provider_reference TEXT,
    request_fingerprint TEXT,
    response_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (operation_type, idempotency_key)
);

-- 9. Provider events are persisted before domain processing.
CREATE TABLE IF NOT EXISTS provider_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name TEXT NOT NULL,
    provider_event_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    signature_verified BOOLEAN NOT NULL DEFAULT FALSE,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    occurred_at TIMESTAMPTZ,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    processing_status TEXT NOT NULL DEFAULT 'RECEIVED',
    processed_at TIMESTAMPTZ,
    processing_error TEXT,
    UNIQUE (provider_name, provider_event_id)
);

CREATE INDEX IF NOT EXISTS ix_provider_events_status_received
    ON provider_events(processing_status, received_at);

-- 10. Settlement and reconciliation are separate from payment execution.
CREATE TABLE IF NOT EXISTS settlements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name TEXT NOT NULL,
    provider_reference TEXT NOT NULL,
    transaction_id UUID REFERENCES transactions(id),
    amount NUMERIC(20,4) NOT NULL,
    currency CHAR(3) NOT NULL,
    status TEXT NOT NULL,
    settled_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (provider_name, provider_reference)
);

CREATE TABLE IF NOT EXISTS reconciliation_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    settlement_id UUID REFERENCES settlements(id),
    transaction_id UUID REFERENCES transactions(id),
    result TEXT NOT NULL,
    internal_amount NUMERIC(20,4),
    external_amount NUMERIC(20,4),
    internal_currency CHAR(3),
    external_currency CHAR(3),
    discrepancy JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 11. Transactional outbox. Insert this row in the same DB transaction as the state change.
CREATE TABLE IF NOT EXISTS outbox_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    aggregate_type TEXT NOT NULL,
    aggregate_id UUID NOT NULL,
    event_version INTEGER NOT NULL DEFAULT 1,
    payload JSONB NOT NULL,
    correlation_id TEXT,
    causation_id TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING',
    available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at TIMESTAMPTZ,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_outbox_pending
    ON outbox_events(status, available_at)
    WHERE status = 'PENDING';

-- 12. Double-entry-ready accounting primitives.
CREATE TABLE IF NOT EXISTS ledger_journals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID REFERENCES transactions(id),
    journal_type TEXT NOT NULL,
    currency CHAR(3) NOT NULL,
    idempotency_key TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'POSTED',
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (journal_type, idempotency_key)
);

CREATE TABLE IF NOT EXISTS ledger_postings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_id UUID NOT NULL REFERENCES ledger_journals(id),
    ledger_account_id UUID NOT NULL REFERENCES ledger_accounts(id),
    direction TEXT NOT NULL CHECK (direction IN ('DEBIT', 'CREDIT')),
    amount NUMERIC(20,4) NOT NULL,
    currency CHAR(3) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (amount > 0)
);

CREATE INDEX IF NOT EXISTS ix_ledger_postings_journal
    ON ledger_postings(journal_id);

-- 13. Useful integrity indexes.
CREATE INDEX IF NOT EXISTS ix_authorization_evidence_agent
    ON authorization_evidence(agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_budget_reservations_payment
    ON budget_reservations(payment_request_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_provider_operations_payment
    ON provider_operations(payment_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_settlements_transaction
    ON settlements(transaction_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_reconciliation_transaction
    ON reconciliation_records(transaction_id, created_at DESC);

-- NOTE: double-entry balance is enforced by the application transaction in V1.
-- A future migration may add a deferred PostgreSQL constraint/trigger once the
-- journal posting workflow is frozen. Never infer accounting truth from wallet.balance.
