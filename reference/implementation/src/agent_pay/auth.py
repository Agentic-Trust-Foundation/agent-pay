"""Authentication boundary for the reference implementation.

Production deployments should replace these development resolvers with OIDC/JWT
verification, separate human approval authentication, and policy-aware authorization.
"""
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Principal:
    agent_id: str
    account_id: str
    scopes: frozenset[str]


def resolve_bearer(token: str | None) -> Principal:
    mode = os.getenv("AGENT_PAY_AUTH_MODE", "strict")
    if mode == "development":
        expected = os.getenv("AGENT_PAY_DEV_TOKEN", "local-agent-token")
        if token != expected:
            raise PermissionError("invalid development bearer token")
        agent_id = os.getenv("AGENT_PAY_DEV_AGENT_ID")
        account_id = os.getenv("AGENT_PAY_DEV_ACCOUNT_ID")
        if not agent_id or not account_id:
            raise PermissionError("development principal is not configured")
        return Principal(agent_id, account_id, frozenset({"payments:create", "payments:read"}))
    raise PermissionError("production authentication adapter is not configured")


def resolve_approval_bearer(token: str | None) -> str:
    if os.getenv("AGENT_PAY_AUTH_MODE", "strict") != "development":
        raise PermissionError("production approval authentication adapter is not configured")
    expected = os.getenv("AGENT_PAY_APPROVAL_TOKEN", "local-approval-token")
    if token != expected:
        raise PermissionError("invalid development approval bearer token")
    return os.getenv("AGENT_PAY_APPROVAL_ACTOR", "local-user")


def require_agent(principal: Principal, claimed_agent_id: str, claimed_account_id: str) -> None:
    if principal.agent_id != claimed_agent_id or principal.account_id != claimed_account_id:
        raise PermissionError("authenticated principal does not match payment actor")
    if "payments:create" not in principal.scopes:
        raise PermissionError("principal lacks payments:create scope")
