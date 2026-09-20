-- Agent-Pay V1 authorization-evidence integrity.
-- Signed ATF evidence must be verified before it can authorize a payment request.

ALTER TABLE authorization_evidence
    ADD CONSTRAINT authorization_evidence_verification_status_ck
    CHECK (verification_status IN ('UNVERIFIED', 'VERIFIED', 'REJECTED'));

CREATE OR REPLACE FUNCTION reject_unverified_payment_authority() RETURNS trigger AS $$
BEGIN
    IF NEW.authorization_evidence_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1
              FROM authorization_evidence ae
             WHERE ae.id = NEW.authorization_evidence_id
               AND ae.verification_status = 'VERIFIED'
        ) THEN
            RAISE EXCEPTION 'payment request requires verified authorization evidence';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_payment_request_verified_authority ON payment_requests;
CREATE TRIGGER trg_payment_request_verified_authority
BEFORE INSERT OR UPDATE OF authorization_evidence_id ON payment_requests
FOR EACH ROW EXECUTE FUNCTION reject_unverified_payment_authority();

CREATE INDEX IF NOT EXISTS ix_authorization_evidence_verified
    ON authorization_evidence(verification_status, created_at DESC);
