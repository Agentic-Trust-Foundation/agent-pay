-- Agent-Pay Phase 13: ledger posting and settlement reconciliation integrity.
-- Apply after 014_provider_operation_recovery.sql.

-- Financial journals and settlements must carry canonical ISO-4217 style
-- three-letter uppercase currencies and strictly positive amounts.
ALTER TABLE ledger_journals
    ADD CONSTRAINT ck_ledger_journals_currency
    CHECK (currency = upper(currency) AND char_length(currency) = 3);

ALTER TABLE ledger_postings
    ADD CONSTRAINT ck_ledger_postings_currency
    CHECK (currency = upper(currency) AND char_length(currency) = 3);

ALTER TABLE settlements
    ADD CONSTRAINT ck_settlements_amount_positive
    CHECK (amount > 0);

ALTER TABLE settlements
    ADD CONSTRAINT ck_settlements_currency
    CHECK (currency = upper(currency) AND char_length(currency) = 3);

-- V1 reconciliation outcomes are intentionally explicit. A discrepancy is
-- evidence for investigation, never an automatic financial mutation.
ALTER TABLE reconciliation_records
    ADD CONSTRAINT ck_reconciliation_status
    CHECK (status IN ('MATCHED', 'DISCREPANCY'));

-- Provider references must not silently select an arbitrary operation. Keep
-- the existing non-unique index because provider references are scoped by the
-- external provider, while the application now treats multiple internal
-- matches as an ambiguity/discrepancy.
CREATE INDEX IF NOT EXISTS ix_provider_operations_reference_lookup
    ON provider_operations(provider_reference)
    WHERE provider_reference IS NOT NULL;

-- Enforce balanced double-entry journals at transaction commit. This is
-- intentionally deferred because a valid journal is created before its
-- postings inside one transaction.
CREATE OR REPLACE FUNCTION assert_ledger_journal_balanced()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    target_journal UUID;
    posting_count INTEGER;
    debit_total NUMERIC(20,4);
    credit_total NUMERIC(20,4);
    journal_currency CHAR(3);
BEGIN
    IF TG_TABLE_NAME = 'ledger_journals' THEN
        target_journal := CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END;
    ELSE
        target_journal := CASE WHEN TG_OP = 'DELETE' THEN OLD.journal_id ELSE NEW.journal_id END;
    END IF;

    SELECT currency
      INTO journal_currency
      FROM ledger_journals
     WHERE id = target_journal;

    IF journal_currency IS NULL THEN
        RAISE EXCEPTION 'ledger journal % does not exist', target_journal;
    END IF;

    SELECT count(*),
           COALESCE(SUM(CASE WHEN side = 'DEBIT' THEN amount ELSE 0 END), 0),
           COALESCE(SUM(CASE WHEN side = 'CREDIT' THEN amount ELSE 0 END), 0)
      INTO posting_count, debit_total, credit_total
      FROM ledger_postings
     WHERE journal_id = target_journal;

    IF posting_count = 0 OR debit_total <= 0 OR credit_total <= 0 OR debit_total <> credit_total THEN
        RAISE EXCEPTION 'ledger journal % is not balanced', target_journal;
    END IF;

    IF EXISTS (
        SELECT 1
          FROM ledger_postings
         WHERE journal_id = target_journal
           AND currency <> journal_currency
    ) THEN
        RAISE EXCEPTION 'ledger journal % contains a currency mismatch', target_journal;
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_ledger_journal_balanced ON ledger_journals;
CREATE CONSTRAINT TRIGGER trg_ledger_journal_balanced
AFTER INSERT OR UPDATE
ON ledger_journals
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION assert_ledger_journal_balanced();

DROP TRIGGER IF EXISTS trg_ledger_postings_balanced ON ledger_postings;
CREATE CONSTRAINT TRIGGER trg_ledger_postings_balanced
AFTER INSERT OR UPDATE OR DELETE
ON ledger_postings
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION assert_ledger_journal_balanced();
