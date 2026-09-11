"""Authentication boundary for the reference implementation.

The reference implementation deliberately keeps credential verification outside the
payment domain. Production deployments should replace the development resolver with
OIDC/JWT verification and bind the authenticated principal to the claimed agent.
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


def require_agent(principal: Principal, claimed_agent_id: str, claimed_account_id: str) -> None:
    if principal.agent_id != claimed_agent_id or principal.account_id != claimed_account_id:
        raise PermissionError("authenticated principal does not match payment actor")
    if "payments:create" not in principal.scopes:
        raise PermissionError("principal lacks payments:create scope")
