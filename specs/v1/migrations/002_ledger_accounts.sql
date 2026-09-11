-- Agent-Pay V1: general-purpose ledger accounts for double-entry settlement.
-- Apply after 001_stage4_convergence.sql.

ALTER TABLE ledger_accounts
    ALTER COLUMN wallet_id DROP NOT NULL;

ALTER TABLE ledger_accounts
    ADD COLUMN IF NOT EXISTS account_type TEXT NOT NULL DEFAULT 'WALLET';

ALTER TABLE ledger_accounts
    ADD COLUMN IF NOT EXISTS name TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS ux_ledger_accounts_non_wallet_name
    ON ledger_accounts (account_type, currency, name)
    WHERE wallet_id IS NULL AND name IS NOT NULL;

CREATE TABLE IF NOT EXISTS payment_provider_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name TEXT NOT NULL,
    currency CHAR(3) NOT NULL,
    ledger_account_id UUID NOT NULL UNIQUE REFERENCES ledger_accounts(id),
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (provider_name, currency)
);

-- New ledger postings may target either a wallet ledger account or a system/provider
-- clearing account. Wallet-linked accounts remain the default customer-money account.
