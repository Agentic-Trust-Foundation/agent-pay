-- Stage 9: payment-instrument lifecycle and account-binding integrity.
-- Apply after 008_reconciliation_multiple_settlements.sql.

CREATE TYPE payment_instrument_status AS ENUM ('ACTIVE', 'SUSPENDED', 'CLOSED');

ALTER TABLE payment_instruments
    ALTER COLUMN status DROP DEFAULT;

ALTER TABLE payment_instruments
    ALTER COLUMN status TYPE payment_instrument_status
    USING status::payment_instrument_status;

ALTER TABLE payment_instruments
    ALTER COLUMN status SET DEFAULT 'ACTIVE';

-- A wallet can be represented by at most one instrument for an account.
CREATE UNIQUE INDEX IF NOT EXISTS ux_payment_instrument_wallet_account
    ON payment_instruments(account_id, wallet_id)
    WHERE wallet_id IS NOT NULL;

-- Provider references are opaque identifiers scoped to an Agent-Pay account.
CREATE UNIQUE INDEX IF NOT EXISTS ux_payment_instrument_provider_reference
    ON payment_instruments(account_id, provider_reference)
    WHERE provider_reference IS NOT NULL;

-- A wallet-backed instrument must point at a wallet owned by the same account.
CREATE OR REPLACE FUNCTION validate_payment_instrument_wallet_account()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.wallet_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM wallets w
        WHERE w.id = NEW.wallet_id AND w.account_id = NEW.account_id
    ) THEN
        RAISE EXCEPTION 'payment instrument wallet must belong to the same account';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_payment_instrument_wallet_account ON payment_instruments;
CREATE TRIGGER trg_payment_instrument_wallet_account
BEFORE INSERT OR UPDATE OF account_id, wallet_id ON payment_instruments
FOR EACH ROW EXECUTE FUNCTION validate_payment_instrument_wallet_account();

-- A payment instrument may only reference a funding source owned by the same account.
CREATE OR REPLACE FUNCTION validate_payment_instrument_funding_account()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.funding_source_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM funding_sources f
        WHERE f.id = NEW.funding_source_id AND f.account_id = NEW.account_id
    ) THEN
        RAISE EXCEPTION 'payment instrument funding source must belong to the same account';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_payment_instrument_funding_account ON payment_instruments;
CREATE TRIGGER trg_payment_instrument_funding_account
BEFORE INSERT OR UPDATE OF account_id, funding_source_id ON payment_instruments
FOR EACH ROW EXECUTE FUNCTION validate_payment_instrument_funding_account();

COMMENT ON TABLE payment_instruments IS
'Controlled payment instruments. Provider references are opaque; credentials are never stored here.';
