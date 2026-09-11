import pytest

from agent_pay.auth import Principal, require_agent, resolve_bearer


def test_strict_mode_fails_closed(monkeypatch):
    monkeypatch.delenv("AGENT_PAY_AUTH_MODE", raising=False)
    with pytest.raises(PermissionError, match="not configured"):
        resolve_bearer("anything")


def test_principal_must_match_claims():
    principal = Principal("agent-1", "account-1", frozenset({"payments:create"}))
    require_agent(principal, "agent-1", "account-1")
    with pytest.raises(PermissionError):
        require_agent(principal, "agent-2", "account-1")
