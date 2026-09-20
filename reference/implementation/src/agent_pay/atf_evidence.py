"""Reference cryptographic verifier for ATF authorization evidence.

This is an implementation profile, not a universal ATF wire format. It verifies
an ATF V1 authorization decision carried as a signed JWT using a configured JWKS,
issuer, and audience, then converts the verified claims into Agent-Pay's
normalized AuthorizationContext.
"""
from decimal import Decimal, InvalidOperation
import hashlib
import os

import jwt
from jwt import PyJWKClient

from .authorization import AuthorizationContext, AuthorizationError


class ATFEvidenceVerificationError(AuthorizationError):
    """Raised when signed ATF evidence cannot establish financial authority."""


def verify_signed_assertion(
    assertion: str,
    *,
    expected_agent_id: str,
    expected_account_id: str,
    amount: Decimal,
    currency: str,
) -> AuthorizationContext:
    jwks_url = os.getenv("AGENT_PAY_ATF_JWKS_URL")
    issuer = os.getenv("AGENT_PAY_ATF_ISSUER")
    audience = os.getenv("AGENT_PAY_ATF_AUDIENCE")
    if not jwks_url or not issuer or not audience:
        raise ATFEvidenceVerificationError(
            "ATF evidence verification is not fully configured"
        )
    if not assertion:
        raise ATFEvidenceVerificationError("signed ATF authorization evidence is required")

    try:
        key = PyJWKClient(jwks_url).get_signing_key_from_jwt(assertion)
        claims = jwt.decode(
            assertion,
            key.key,
            algorithms=["RS256", "ES256", "EdDSA"],
            audience=audience,
            issuer=issuer,
            options={
                "require": [
                    "exp", "iat", "iss", "aud", "sub",
                    "evidence_id", "protocol_version", "decision",
                    "subject_agent", "account_id", "action",
                    "max_amount", "currency", "version",
                    "revocation_status",
                ]
            },
        )
    except jwt.PyJWTError as exc:
        raise ATFEvidenceVerificationError("invalid signed ATF authorization evidence") from exc

    if claims.get("protocol_version") != "atf/v1":
        raise ATFEvidenceVerificationError("unsupported ATF protocol version")
    if claims.get("decision") != "ALLOW":
        raise ATFEvidenceVerificationError("ATF authorization decision does not allow payment")
    if claims.get("action") != "PAYMENT":
        raise ATFEvidenceVerificationError("ATF authorization action is not PAYMENT")
    if claims.get("revocation_status") != "VALID":
        raise ATFEvidenceVerificationError("ATF authorization evidence is not currently valid")
    if claims.get("subject_agent") != expected_agent_id:
        raise ATFEvidenceVerificationError("ATF evidence subject does not match agent")
    if claims.get("account_id") != expected_account_id:
        raise ATFEvidenceVerificationError("ATF evidence account does not match payment account")

    raw_scope = claims.get("scope", ["PAYMENT"])
    if isinstance(raw_scope, str):
        scope = frozenset(raw_scope.split())
    elif isinstance(raw_scope, list):
        scope = frozenset(str(item) for item in raw_scope)
    else:
        scope = frozenset()
    if "PAYMENT" not in scope:
        raise ATFEvidenceVerificationError("ATF evidence does not grant PAYMENT scope")

    try:
        max_amount = Decimal(str(claims["max_amount"]))
    except (InvalidOperation, TypeError) as exc:
        raise ATFEvidenceVerificationError("ATF maximum amount is invalid") from exc
    if max_amount <= 0:
        raise ATFEvidenceVerificationError("ATF maximum amount must be positive")

    evidence_currency = str(claims["currency"]).upper()
    if len(evidence_currency) != 3 or evidence_currency != currency.upper():
        raise ATFEvidenceVerificationError("ATF currency does not match payment currency")
    if amount <= 0 or amount > max_amount:
        raise ATFEvidenceVerificationError("payment exceeds ATF authorized amount")

    valid_until = claims.get("exp")
    if valid_until is None:
        raise ATFEvidenceVerificationError("ATF evidence expiry is required")

    return AuthorizationContext(
        evidence_id=str(claims["evidence_id"]),
        issuer=str(claims["iss"]),
        agent_id=expected_agent_id,
        account_id=expected_account_id,
        delegation_id=str(claims["delegation_id"]) if claims.get("delegation_id") else None,
        scope=scope,
        max_amount=max_amount,
        currency=evidence_currency,
        valid_until=jwt.utils.datetime_from_timestamp(valid_until),
        digest=hashlib.sha256(assertion.encode("utf-8")).hexdigest(),
        version=str(claims["version"]),
    )
