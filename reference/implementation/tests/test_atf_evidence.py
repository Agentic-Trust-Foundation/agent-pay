import time
from decimal import Decimal

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from agent_pay.atf_evidence import verify_signed_assertion, ATFEvidenceVerificationError


def _configure(monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setenv("AGENT_PAY_ATF_JWKS_URL", "https://atf.example/jwks.json")
    monkeypatch.setenv("AGENT_PAY_ATF_ISSUER", "https://atf.example/")
    monkeypatch.setenv("AGENT_PAY_ATF_AUDIENCE", "agent-pay")

    public_key = key.public_key()
    class SigningKey:
        pass
    signing_key = SigningKey()
    signing_key.key = public_key

    class FakeJWKClient:
        def __init__(self, url):
            assert url == "https://atf.example/jwks.json"

        def get_signing_key_from_jwt(self, token):
            return signing_key

    monkeypatch.setattr("agent_pay.atf_evidence.PyJWKClient", FakeJWKClient)
    return key


def _token(key, **overrides):
    now = int(time.time())
    claims = {
        "iss": "https://atf.example/",
        "aud": "agent-pay",
        "sub": "decision-subject",
        "iat": now,
        "exp": now + 300,
        "evidence_id": "ev-1",
        "protocol_version": "atf/v1",
        "decision": "ALLOW",
        "subject_agent": "agent-1",
        "account_id": "account-1",
        "action": "PAYMENT",
        "scope": ["PAYMENT"],
        "max_amount": "100.00",
        "currency": "USD",
        "version": "v1",
        "revocation_status": "VALID",
    }
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm="RS256")


def test_valid_signed_evidence_is_verified(monkeypatch):
    key = _configure(monkeypatch)
    context = verify_signed_assertion(
        _token(key),
        expected_agent_id="agent-1",
        expected_account_id="account-1",
        amount=Decimal("75"),
        currency="USD",
    )
    assert context.evidence_id == "ev-1"
    assert context.version == "v1"
    assert context.digest


@pytest.mark.parametrize(
    "overrides",
    [
        {"decision": "DENY"},
        {"revocation_status": "REVOKED"},
        {"action": "BOOKING"},
        {"subject_agent": "other-agent"},
        {"account_id": "other-account"},
        {"max_amount": "50.00"},
        {"currency": "EUR"},
    ],
)
def test_invalid_authority_claims_fail_closed(monkeypatch, overrides):
    key = _configure(monkeypatch)
    with pytest.raises(ATFEvidenceVerificationError):
        verify_signed_assertion(
            _token(key, **overrides),
            expected_agent_id="agent-1",
            expected_account_id="account-1",
            amount=__import__("decimal").Decimal("75"),
            currency="USD",
        )


def test_missing_configuration_fails_closed(monkeypatch):
    for name in (
        "AGENT_PAY_ATF_JWKS_URL",
        "AGENT_PAY_ATF_ISSUER",
        "AGENT_PAY_ATF_AUDIENCE",
    ):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ATFEvidenceVerificationError, match="not fully configured"):
        verify_signed_assertion(
            "token",
            expected_agent_id="agent-1",
            expected_account_id="account-1",
            amount=Decimal("1"),
            currency="USD",
        )
