-- Agent-Pay V1 PostgreSQL schema
-- Design status: implementation-oriented draft.
-- Financial truth lives in ledger_entries; wallet balances are derived/cached state.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE account_status AS ENUM ('ACTIVE', 'SUSPENDED', 'CLOSED');
CREATE TYPE agent_status AS ENUM ('ACTIVE', 'SUSPENDED', 'REVOKED');
CREATE TYPE delegation_status AS ENUM ('ACTIVE', 'SUSPENDED', 'REVOKED', 'EXPIRED');
CREATE TYPE wallet_status AS ENUM ('ACTIVE', 'SUSPENDED', 'CLOSED');
CREATE TYPE policy_status AS ENUM ('ACTIVE', 'INACTIVE');
CREATE TYPE approval_status AS ENUM ('PENDING', 'APPROVED', 'DENIED', 'EXPIRED', 'CANCELLED');
CREATE TYPE payment_status AS ENUM ('REQUESTED', 'VALIDATING', 'POLICY_CHECK', 'BUDGET_CHECK', 'APPROVAL_REQUIRED', 'APPROVED', 'PAYMENT_PENDING', 'PROCESSING', 'SUCCEEDED', 'FAILED', 'CANCELLED', 'REFUND_REQUESTED', 'REFUNDED');
CREATE TYPE transaction_status AS ENUM ('PENDING', 'POSTED', 'FAILED', 'REVERSED');
CREATE TYPE ledger_entry_type AS ENUM ('CREDIT', 'DEBIT', 'HOLD', 'RELEASE', 'REFUND', 'ADJUSTMENT');
CREATE TYPE ledger_entry_status AS ENUM ('PENDING', 'POSTED', 'VOIDED');
CREATE TYPE instrument_type AS ENUM ('WALLET', 'VIRTUAL_CARD', 'BANK_ACCOUNT', 'PAYMENT_GATEWAY', 'OTHER');

CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_reference TEXT NOT NULL,
    status account_status NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    name TEXT NOT NULL,
    identity_reference TEXT,
    status agent_status NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE delegations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    agent_id UUID NOT NULL REFERENCES agents(id),
    scope JSONB NOT NULL DEFAULT '{}'::jsonb,
    constraints JSONB NOT NULL DEFAULT '{}'::jsonb,
    status delegation_status NOT NULL DEFAULT 'ACTIVE',
    valid_from TIMESTAMPTZ,
    valid_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (valid_until IS NULL OR valid_from IS NULL OR valid_until > valid_from)
);

CREATE TABLE wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    currency CHAR(3) NOT NULL,
    status wallet_status NOT NULL DEFAULT 'ACTIVE',
    -- Cached/derived values only. Ledger remains authoritative.
    balance NUMERIC(20,4) NOT NULL DEFAULT 0,
    available_balance NUMERIC(20,4) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (balance >= 0),
    CHECK (available_balance >= 0),
    CHECK (available_balance <= balance)
);

CREATE TABLE ledger_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID NOT NULL UNIQUE REFERENCES wallets(id),
    currency CHAR(3) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE funding_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    type TEXT NOT NULL,
    provider_reference TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE payment_instruments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    type instrument_type NOT NULL,
    wallet_id UUID REFERENCES wallets(id),
    funding_source_id UUID REFERENCES funding_sources(id),
    provider_reference TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (wallet_id IS NOT NULL OR funding_source_id IS NOT NULL OR provider_reference IS NOT NULL)
);

CREATE TABLE merchants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    domain TEXT,
    category TEXT,
    country CHAR(2),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    name TEXT NOT NULL,
    rules JSONB NOT NULL DEFAULT '{}'::jsonb,
    status policy_status NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    policy_id UUID REFERENCES policies(id),
    name TEXT NOT NULL,
    currency CHAR(3) NOT NULL,
    limit_amount NUMERIC(20,4) NOT NULL,
    consumed_amount NUMERIC(20,4) NOT NULL DEFAULT 0,
    reserved_amount NUMERIC(20,4) NOT NULL DEFAULT 0,
    period_start TIMESTAMPTZ,
    period_end TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (limit_amount >= 0),
    CHECK (consumed_amount >= 0),
    CHECK (reserved_amount >= 0),
    CHECK (period_end IS NULL OR period_start IS NULL OR period_end > period_start)
);

CREATE TABLE payment_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    agent_id UUID NOT NULL REFERENCES agents(id),
    merchant_id UUID REFERENCES merchants(id),
    amount NUMERIC(20,4) NOT NULL,
    currency CHAR(3) NOT NULL,
    purpose TEXT NOT NULL,
    items JSONB NOT NULL DEFAULT '[]'::jsonb,
    idempotency_key TEXT NOT NULL,
    authorization_context JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (amount > 0),
    UNIQUE (account_id, idempotency_key)
);

CREATE TABLE approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_request_id UUID NOT NULL UNIQUE REFERENCES payment_requests(id),
    status approval_status NOT NULL DEFAULT 'PENDING',
    requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ,
    approved_at TIMESTAMPTZ,
    approved_by TEXT,
    reason TEXT,
    CHECK (expires_at IS NULL OR expires_at > requested_at)
);

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_request_id UUID NOT NULL UNIQUE REFERENCES payment_requests(id),
    payment_instrument_id UUID REFERENCES payment_instruments(id),
    amount NUMERIC(20,4) NOT NULL,
    currency CHAR(3) NOT NULL,
    status payment_status NOT NULL DEFAULT 'REQUESTED',
    provider_reference TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (amount > 0)
);

CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID REFERENCES payments(id),
    type TEXT NOT NULL,
    status transaction_status NOT NULL DEFAULT 'PENDING',
    amount NUMERIC(20,4) NOT NULL,
    currency CHAR(3) NOT NULL,
    original_transaction_id UUID REFERENCES transactions(id),
    external_reference TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    posted_at TIMESTAMPTZ,
    CHECK (amount > 0)
);

CREATE TABLE ledger_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ledger_account_id UUID NOT NULL REFERENCES ledger_accounts(id),
    transaction_id UUID REFERENCES transactions(id),
    entry_type ledger_entry_type NOT NULL,
    status ledger_entry_status NOT NULL DEFAULT 'POSTED',
    amount NUMERIC(20,4) NOT NULL,
    currency CHAR(3) NOT NULL,
    reference_type TEXT,
    reference_id UUID,
    idempotency_key TEXT,
    correlation_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (amount > 0)
);

CREATE UNIQUE INDEX ux_ledger_idempotency
    ON ledger_entries (ledger_account_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id),
    actor_type TEXT NOT NULL,
    actor_reference TEXT,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id UUID,
    result TEXT NOT NULL,
    correlation_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    delivered_at TIMESTAMPTZ
);

CREATE INDEX ix_agents_account ON agents(account_id);
CREATE INDEX ix_delegations_agent ON delegations(agent_id);
CREATE INDEX ix_wallets_account ON wallets(account_id);
CREATE INDEX ix_ledger_entries_account_created ON ledger_entries(ledger_account_id, created_at DESC);
CREATE INDEX ix_payment_requests_agent_created ON payment_requests(agent_id, created_at DESC);
CREATE INDEX ix_payments_status_created ON payments(status, created_at DESC);
CREATE INDEX ix_transactions_payment ON transactions(payment_id);
CREATE INDEX ix_audit_events_account_created ON audit_events(account_id, created_at DESC);
CREATE INDEX ix_notifications_account_status ON notifications(account_id, status);
