import os

import jwt
import pytest

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
