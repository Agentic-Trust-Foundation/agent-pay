-- Agent-Pay V1 architecture completion migration
-- Purpose: close schema gaps identified after the initial database draft.
-- This is a design migration draft; review against the final application schema before production use.

-- 1. Explicit payment authentication / extended lifecycle.
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'AUTHENTICATION_REQUIRED';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'AUTHENTICATED';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'UNKNOWN_EXTERNAL_OUTCOME';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'SETTLEMENT_PENDING';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'SETTLED';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'DISPUTED';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'CHARGEBACK';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'REFUND_PROCESSING';
ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'REFUND_FAILED';

-- 2. Versioned policy definitions and deterministic decision evidence.
ALTER TABLE policies
    ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS scope JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE UNIQUE INDEX IF NOT EXISTS ux_policy_version
    ON policies(id, version);

CREATE TABLE IF NOT EXISTS policy_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_request_id UUID NOT NULL REFERENCES payment_requests(id),
    decision TEXT NOT NULL CHECK (decision IN ('ALLOW_AUTO','ALLOW_NOTIFY','REQUIRE_APPROVAL','DENY')),
    policy_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    reason_codes JSONB NOT NULL DEFAULT '[]'::jsonb,
    decision_trace JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Budget reservations are separate from wallet/provider holds.
CREATE TABLE IF NOT EXISTS budget_reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    budget_id UUID NOT NULL REFERENCES budgets(id),
    payment_request_id UUID NOT NULL REFERENCES payment_requests(id),
    amount NUMERIC(20,4) NOT NULL,
    currency CHAR(3) NOT NULL,
    status TEXT NOT NULL DEFAULT 'RESERVED'
        CHECK (status IN ('RESERVED','CONSUMED','RELEASED','EXPIRED')),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (budget_id, payment_request_id),
    CHECK (amount > 0)
);

CREATE INDEX IF NOT EXISTS ix_budget_reservations_payment
    ON budget_reservations(payment_request_id);

-- 4. Transactional outbox for reliable internal event publication.
CREATE TABLE IF NOT EXISTS outbox_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    event_version INTEGER NOT NULL DEFAULT 1,
    aggregate_type TEXT NOT NULL,
    aggregate_id UUID NOT NULL,
    correlation_id TEXT,
    causation_id TEXT,
    idempotency_key TEXT,
    payload JSONB NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at TIMESTAMPTZ,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT
);

CREATE INDEX IF NOT EXISTS ix_outbox_unpublished
    ON outbox_events(occurred_at)
    WHERE published_at IS NULL;

-- 5. Persist provider events before applying them to financial state.
CREATE TABLE IF NOT EXISTS provider_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name TEXT NOT NULL,
    provider_event_id TEXT,
    event_type TEXT NOT NULL,
    payment_id UUID REFERENCES payments(id),
    external_reference TEXT,
    payload JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at TIMESTAMPTZ,
    processing_status TEXT NOT NULL DEFAULT 'RECEIVED'
        CHECK (processing_status IN ('RECEIVED','PROCESSED','DEFERRED','REJECTED','FAILED')),
    processing_error TEXT,
    UNIQUE (provider_name, provider_event_id)
);

CREATE INDEX IF NOT EXISTS ix_provider_events_payment
    ON provider_events(payment_id, received_at DESC);

-- 6. Explicit reconciliation outcomes.
CREATE TABLE IF NOT EXISTS reconciliation_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID REFERENCES payments(id),
    transaction_id UUID REFERENCES transactions(id),
    provider_name TEXT NOT NULL,
    provider_reference TEXT,
    outcome TEXT NOT NULL CHECK (outcome IN (
        'MATCHED',
        'PENDING',
        'UNMATCHED_INTERNAL',
        'UNMATCHED_PROVIDER',
        'AMOUNT_MISMATCH',
        'CURRENCY_MISMATCH',
        'STATUS_MISMATCH',
        'REFERENCE_MISMATCH',
        'DUPLICATE',
        'REQUIRES_REVIEW'
    )),
    internal_amount NUMERIC(20,4),
    provider_amount NUMERIC(20,4),
    internal_currency CHAR(3),
    provider_currency CHAR(3),
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_reconciliation_payment
    ON reconciliation_records(payment_id, created_at DESC);

-- 7. Explicit payment authentication records.
CREATE TABLE IF NOT EXISTS payment_authentications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES payments(id),
    provider_name TEXT,
    authentication_reference TEXT,
    status TEXT NOT NULL
        CHECK (status IN ('REQUIRED','STARTED','COMPLETED','FAILED','EXPIRED')),
    challenge_reference TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_payment_auth_payment
    ON payment_authentications(payment_id, created_at DESC);

-- 8. Lightweight commerce context references; Agent-Pay does not own order/fulfillment state.
ALTER TABLE payment_requests
    ADD COLUMN IF NOT EXISTS commerce_context JSONB NOT NULL DEFAULT '{}'::jsonb;

-- 9. Provider operation identity for safe recovery and reconciliation.
ALTER TABLE payments
    ADD COLUMN IF NOT EXISTS provider_name TEXT,
    ADD COLUMN IF NOT EXISTS operation_reference TEXT,
    ADD COLUMN IF NOT EXISTS authorization_reference TEXT,
    ADD COLUMN IF NOT EXISTS capture_reference TEXT;

CREATE INDEX IF NOT EXISTS ix_payments_provider_operation
    ON payments(provider_name, operation_reference)
    WHERE operation_reference IS NOT NULL;

-- 10. Future authorization evidence reference without making Agent-Pay the identity system.
ALTER TABLE payment_requests
    ADD COLUMN IF NOT EXISTS authorization_evidence_reference TEXT;

ALTER TABLE approvals
    ADD COLUMN IF NOT EXISTS policy_version INTEGER,
    ADD COLUMN IF NOT EXISTS authorization_evidence_reference TEXT;

-- Financial history remains append-oriented. Do not update/delete historical ledger entries
-- to correct financial state; use compensating entries or adjustments.
