"""Authentication boundary for the reference implementation.

Development mode is intentionally simple. Production mode verifies a short-lived
OIDC/OAuth2 JWT using the provider JWKS, issuer, audience, and required scopes.
The resulting principal is still bound to the claimed Agent-Pay agent/account.
"""
from dataclasses import dataclass
import os

import jwt
from jwt import PyJWKClient


@dataclass(frozen=True)
class Principal:
    agent_id: str
    account_id: str
    scopes: frozenset[str]
    subject: str | None = None
    issuer: str | None = None


def _oidc_principal(token: str) -> Principal:
    jwks_url = os.getenv("AGENT_PAY_OIDC_JWKS_URL")
    issuer = os.getenv("AGENT_PAY_OIDC_ISSUER")
    audience = os.getenv("AGENT_PAY_OIDC_AUDIENCE")
    if not jwks_url or not issuer or not audience:
        raise PermissionError("OIDC authentication is not fully configured")

    try:
        signing_key = PyJWKClient(jwks_url).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience=audience,
            issuer=issuer,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        )
    except jwt.PyJWTError as exc:
        raise PermissionError("invalid OIDC bearer token") from exc

    agent_id = claims.get("agent_id")
    account_id = claims.get("account_id")
    if not isinstance(agent_id, str) or not isinstance(account_id, str):
        raise PermissionError("OIDC token is missing Agent-Pay identity claims")

    raw_scopes = claims.get("scope", "")
    scopes = frozenset(raw_scopes.split()) if isinstance(raw_scopes, str) else frozenset()
    return Principal(
        agent_id=agent_id,
        account_id=account_id,
        scopes=scopes,
        subject=claims["sub"],
        issuer=claims["iss"],
    )


def resolve_bearer(token: str | None) -> Principal:
    mode = os.getenv("AGENT_PAY_AUTH_MODE", "strict")
    if not token:
        raise PermissionError("bearer token is required")
    if mode == "development":
        expected = os.getenv("AGENT_PAY_DEV_TOKEN", "local-agent-token")
        if token != expected:
            raise PermissionError("invalid development bearer token")
        agent_id = os.getenv("AGENT_PAY_DEV_AGENT_ID")
        account_id = os.getenv("AGENT_PAY_DEV_ACCOUNT_ID")
        if not agent_id or not account_id:
            raise PermissionError("development principal is not configured")
        return Principal(agent_id, account_id, frozenset({"payments:create", "payments:read"}))
    if mode == "oidc":
        return _oidc_principal(token)
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
