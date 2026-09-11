import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from agent_pay.auth import Principal, require_agent, resolve_bearer


def test_production_mode_fails_closed_without_oidc_configuration(monkeypatch):
    monkeypatch.setenv("AGENT_PAY_AUTH_MODE", "oidc")
    for key in ("AGENT_PAY_OIDC_JWKS_URL", "AGENT_PAY_OIDC_ISSUER", "AGENT_PAY_OIDC_AUDIENCE"):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(PermissionError, match="not fully configured"):
        resolve_bearer("token")


def test_require_agent_binds_identity_and_scope():
    principal = Principal("agent-1", "account-1", frozenset({"payments:create"}))
    require_agent(principal, "agent-1", "account-1")
    with pytest.raises(PermissionError):
        require_agent(principal, "agent-2", "account-1")


def test_require_agent_rejects_read_only_principal():
    principal = Principal("agent-1", "account-1", frozenset({"payments:read"}))
    with pytest.raises(PermissionError, match="payments:create"):
        require_agent(principal, "agent-1", "account-1")


def _configure_oidc(monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = key.public_key()
    monkeypatch.setenv("AGENT_PAY_AUTH_MODE", "oidc")
    monkeypatch.setenv("AGENT_PAY_OIDC_JWKS_URL", "https://issuer.example/jwks.json")
    monkeypatch.setenv("AGENT_PAY_OIDC_ISSUER", "https://issuer.example/")
    monkeypatch.setenv("AGENT_PAY_OIDC_AUDIENCE", "agent-pay")

    class FakeSigningKey:
        pass

    signing_key = FakeSigningKey()
    signing_key.key = public_key

    class FakeJWKClient:
        def __init__(self, url):
            assert url.endswith("/jwks.json")

        def get_signing_key_from_jwt(self, token):
            return signing_key

    monkeypatch.setattr("agent_pay.auth.PyJWKClient", FakeJWKClient)
    return key


def test_oidc_accepts_valid_short_lived_token_and_claim_binding(monkeypatch):
    key = _configure_oidc(monkeypatch)
    now = int(time.time())
    token = jwt.encode(
        {"iss": "https://issuer.example/", "aud": "agent-pay", "sub": "user-1", "agent_id": "agent-1", "account_id": "account-1", "scope": "payments:create payments:read", "iat": now, "exp": now + 300},
        key,
        algorithm="RS256",
    )
    principal = resolve_bearer(token)
    assert principal.agent_id == "agent-1"
    assert principal.account_id == "account-1"
    assert principal.subject == "user-1"
    assert "payments:create" in principal.scopes


def test_oidc_rejects_expired_token(monkeypatch):
    key = _configure_oidc(monkeypatch)
    now = int(time.time())
    token = jwt.encode(
        {"iss": "https://issuer.example/", "aud": "agent-pay", "sub": "user-1", "agent_id": "agent-1", "account_id": "account-1", "scope": "payments:create", "iat": now - 120, "exp": now - 60},
        key,
        algorithm="RS256",
    )
    with pytest.raises(PermissionError, match="invalid OIDC bearer token"):
        resolve_bearer(token)


def test_oidc_rejects_wrong_audience(monkeypatch):
    key = _configure_oidc(monkeypatch)
    now = int(time.time())
    token = jwt.encode(
        {"iss": "https://issuer.example/", "aud": "another-service", "sub": "user-1", "agent_id": "agent-1", "account_id": "account-1", "scope": "payments:create", "iat": now, "exp": now + 300},
        key,
        algorithm="RS256",
    )
    with pytest.raises(PermissionError, match="invalid OIDC bearer token"):
        resolve_bearer(token)


def test_oidc_rejects_missing_agent_identity_claims(monkeypatch):
    key = _configure_oidc(monkeypatch)
    now = int(time.time())
    token = jwt.encode(
        {"iss": "https://issuer.example/", "aud": "agent-pay", "sub": "user-1", "scope": "payments:create", "iat": now, "exp": now + 300},
        key,
        algorithm="RS256",
    )
    with pytest.raises(PermissionError, match="missing Agent-Pay identity claims"):
        resolve_bearer(token)
