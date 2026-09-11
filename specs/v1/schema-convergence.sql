-- Agent-Pay V1 Stage 3 convergence migration
-- Additive migration toward the Master Project Schema.

CREATE TYPE budget_reservation_status AS ENUM ('RESERVED','CONSUMED','RELEASED','EXPIRED','CANCELLED');
CREATE TYPE payment_authentication_status AS ENUM ('NOT_REQUIRED','REQUIRED','PENDING','AUTHENTICATED','FAILED','EXPIRED');
CREATE TYPE provider_operation_status AS ENUM ('PENDING','AUTHENTICATION_REQUIRED','PROCESSING','SUCCEEDED','FAILED','UNKNOWN');
CREATE TYPE provider_event_status AS ENUM ('RECEIVED','VERIFIED','PROCESSED','DUPLICATE','REJECTED','QUARANTINED');
CREATE TYPE settlement_status AS ENUM ('PENDING','SETTLED','FAILED','MISMATCHED');
CREATE TYPE reconciliation_status AS ENUM ('OPEN','MATCHED','MISMATCHED','RESOLVED');

CREATE TABLE policy_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID NOT NULL REFERENCES policies(id),
    version INTEGER NOT NULL,
    rules JSONB NOT NULL DEFAULT '{}'::jsonb,
    rules_digest TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (policy_id, version),
    UNIQUE (id, policy_id)
);

ALTER TABLE policies ADD COLUMN IF NOT EXISTS current_version_id UUID;
ALTER TABLE policies ADD CONSTRAINT fk_policies_current_version
    FOREIGN KEY (current_version_id, id) REFERENCES policy_versions(id, policy_id)
    DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE authorization_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    agent_id UUID NOT NULL REFERENCES agents(id),
    delegation_id UUID REFERENCES delegations(id),
    evidence_type TEXT NOT NULL,
    issuer_reference TEXT,
    source_reference TEXT,
    evidence_digest TEXT NOT NULL,
    issued_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (expires_at IS NULL OR issued_at IS NULL OR expires_at > issued_at)
);

CREATE TABLE budget_reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    budget_id UUID NOT NULL REFERENCES budgets(id),
    payment_request_id UUID NOT NULL REFERENCES payment_requests(id),
    amount NUMERIC(20,4) NOT NULL,
    currency CHAR(3) NOT NULL,
    status budget_reservation_status NOT NULL DEFAULT 'RESERVED',
    idempotency_key TEXT NOT NULL,
    expires_at TIMESTAMPTZ,
    reserved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    consumed_at TIMESTAMPTZ,
    released_at TIMESTAMPTZ,
    CHECK (amount > 0),
    UNIQUE (budget_id, idempotency_key)
);
CREATE INDEX ix_budget_reservations_payment ON budget_reservations(payment_request_id);
CREATE INDEX ix_budget_reservations_status ON budget_reservations(budget_id, status);

ALTER TABLE payment_requests
    ADD COLUMN IF NOT EXISTS correlation_id TEXT,
    ADD COLUMN IF NOT EXISTS commerce_context JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS authorization_evidence_id UUID REFERENCES authorization_evidence(id),
    ADD COLUMN IF NOT EXISTS intent_digest TEXT;

ALTER TABLE approvals DROP CONSTRAINT IF EXISTS approvals_payment_request_id_key;
ALTER TABLE approvals
    ADD COLUMN IF NOT EXISTS intent_digest TEXT,
    ADD COLUMN IF NOT EXISTS decided_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS decided_by TEXT;

ALTER TABLE payments
    ADD COLUMN IF NOT EXISTS policy_version_id UUID REFERENCES policy_versions(id),
    ADD COLUMN IF NOT EXISTS budget_reservation_id UUID REFERENCES budget_reservations(id),
    ADD COLUMN IF NOT EXISTS authorization_evidence_id UUID REFERENCES authorization_evidence(id),
    ADD COLUMN IF NOT EXISTS correlation_id TEXT,
    ADD COLUMN IF NOT EXISTS intent_digest TEXT;

CREATE TABLE payment_authentications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES payments(id),
    status payment_authentication_status NOT NULL DEFAULT 'NOT_REQUIRED',
    method TEXT,
    provider_reference TEXT,
    challenge_reference TEXT,
    next_action JSONB NOT NULL DEFAULT '{}'::jsonb,
    expires_at TIMESTAMPTZ,
    authenticated_at TIMESTAMPTZ,
    failure_code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_payment_auth_payment ON payment_authentications(payment_id, created_at DESC);

CREATE TABLE provider_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES payments(id),
    operation_type TEXT NOT NULL,
    provider_name TEXT NOT NULL,
    provider_reference TEXT,
    idempotency_key TEXT NOT NULL,
    status provider_operation_status NOT NULL DEFAULT 'PENDING',
    request_digest TEXT,
    response_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_error_code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (provider_name, idempotency_key)
);
CREATE INDEX ix_provider_operations_payment ON provider_operations(payment_id, created_at DESC);

CREATE TABLE provider_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name TEXT NOT NULL,
    provider_event_id TEXT,
    event_type TEXT NOT NULL,
    status provider_event_status NOT NULL DEFAULT 'RECEIVED',
    signature_verified BOOLEAN NOT NULL DEFAULT false,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    occurred_at TIMESTAMPTZ,
    aggregate_reference TEXT,
    payload_digest TEXT NOT NULL,
    safe_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    processed_at TIMESTAMPTZ,
    error_code TEXT,
    correlation_id TEXT,
    UNIQUE (provider_name, provider_event_id)
);
CREATE INDEX ix_provider_events_status ON provider_events(status, received_at);

CREATE TABLE settlements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID REFERENCES payments(id),
    transaction_id UUID REFERENCES transactions(id),
    provider_name TEXT NOT NULL,
    provider_reference TEXT,
    amount NUMERIC(20,4) NOT NULL,
    currency CHAR(3) NOT NULL,
    status settlement_status NOT NULL DEFAULT 'PENDING',
    settled_at TIMESTAMPTZ,
    reported_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (amount > 0)
);

CREATE TABLE reconciliation_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name TEXT NOT NULL,
    payment_id UUID REFERENCES payments(id),
    transaction_id UUID REFERENCES transactions(id),
    settlement_id UUID REFERENCES settlements(id),
    status reconciliation_status NOT NULL DEFAULT 'OPEN',
    mismatch_type TEXT,
    internal_amount NUMERIC(20,4),
    external_amount NUMERIC(20,4),
    internal_currency CHAR(3),
    external_currency CHAR(3),
    internal_status TEXT,
    external_status TEXT,
    external_reference TEXT,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ,
    resolution TEXT
);

CREATE TABLE outbox_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    event_version INTEGER NOT NULL DEFAULT 1,
    aggregate_type TEXT NOT NULL,
    aggregate_id UUID NOT NULL,
    correlation_id TEXT,
    causation_id TEXT,
    idempotency_key TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at TIMESTAMPTZ,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT
);
CREATE INDEX ix_outbox_unpublished ON outbox_events(occurred_at) WHERE published_at IS NULL;

CREATE TABLE ledger_journals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID REFERENCES transactions(id),
    journal_type TEXT NOT NULL,
    currency CHAR(3) NOT NULL,
    status TEXT NOT NULL DEFAULT 'POSTED',
    idempotency_key TEXT NOT NULL UNIQUE,
    correlation_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    posted_at TIMESTAMPTZ
);

CREATE TABLE ledger_postings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_id UUID NOT NULL REFERENCES ledger_journals(id),
    ledger_account_id UUID NOT NULL REFERENCES ledger_accounts(id),
    direction TEXT NOT NULL CHECK (direction IN ('DEBIT','CREDIT')),
    amount NUMERIC(20,4) NOT NULL,
    currency CHAR(3) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (amount > 0)
);
CREATE INDEX ix_ledger_postings_journal ON ledger_postings(journal_id);
CREATE INDEX ix_ledger_postings_account ON ledger_postings(ledger_account_id, created_at DESC);

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

ALTER TABLE payments ADD COLUMN IF NOT EXISTS provider_operation_id UUID REFERENCES provider_operations(id);
CREATE INDEX ix_payments_unknown_outcome ON payments(status) WHERE status = 'UNKNOWN_EXTERNAL_OUTCOME';
