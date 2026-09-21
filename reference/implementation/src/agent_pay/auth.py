"""Authentication boundary for the reference implementation.

Development mode is intentionally simple but requires explicit credentials.
Production mode verifies a short-lived OIDC/OAuth2 JWT using provider JWKS,
issuer, audience, and required claims. The principal remains bound to the
claimed Agent-Pay agent/account.
"""
from dataclasses import dataclass
import hmac
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


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise PermissionError(f"{name} is not configured")
    return value


def _oidc_principal(token: str) -> Principal:
    jwks_url = _required_env("AGENT_PAY_OIDC_JWKS_URL")
    issuer = _required_env("AGENT_PAY_OIDC_ISSUER")
    audience = _required_env("AGENT_PAY_OIDC_AUDIENCE")

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
    except Exception as exc:
        # Do not leak key-fetch, parsing, or token-validation details to callers.
        raise PermissionError("invalid OIDC bearer token") from exc

    agent_id = claims.get("agent_id")
    account_id = claims.get("account_id")
    if not isinstance(agent_id, str) or not agent_id.strip():
        raise PermissionError("OIDC token is missing Agent-Pay identity claims")
    if not isinstance(account_id, str) or not account_id.strip():
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
        expected = _required_env("AGENT_PAY_DEV_TOKEN")
        if not hmac.compare_digest(token, expected):
            raise PermissionError("invalid development bearer token")
        agent_id = _required_env("AGENT_PAY_DEV_AGENT_ID")
        account_id = _required_env("AGENT_PAY_DEV_ACCOUNT_ID")
        return Principal(agent_id, account_id, frozenset({"payments:create", "payments:read"}))
    if mode == "oidc":
        return _oidc_principal(token)
    raise PermissionError("production authentication adapter is not configured")


def resolve_approval_bearer(token: str | None) -> str:
    if os.getenv("AGENT_PAY_AUTH_MODE", "strict") != "development":
        raise PermissionError("production approval authentication adapter is not configured")
    expected = _required_env("AGENT_PAY_APPROVAL_TOKEN")
    if not token or not hmac.compare_digest(token, expected):
        raise PermissionError("invalid development approval bearer token")
    return _required_env("AGENT_PAY_APPROVAL_ACTOR")


def require_agent(principal: Principal, claimed_agent_id: str, claimed_account_id: str) -> None:
    if principal.agent_id != claimed_agent_id or principal.account_id != claimed_account_id:
        raise PermissionError("authenticated principal does not match payment actor")
    if "payments:create" not in principal.scopes:
        raise PermissionError("principal lacks payments:create scope")
