"""Normalized authorization-evidence contract between ATF and Agent-Pay.

The financial engine consumes this context; it does not mint or verify a
protocol-specific cryptographic token. Adapters are responsible for translating
upstream ATF/delegation evidence into this normalized representation.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal


class AuthorizationError(PermissionError):
    """Raised when financial authority cannot be safely established."""


@dataclass(frozen=True)
class AuthorizationContext:
    evidence_id: str
    issuer: str
    agent_id: str
    account_id: str
    delegation_id: str | None = None
    scope: frozenset[str] = frozenset()
    max_amount: Decimal | None = None
    currency: str | None = None
    valid_until: datetime | None = None
    digest: str | None = None
    version: str | None = None

    def validate(self, *, agent_id: str, account_id: str,
                 amount: Decimal, currency: str,
                 action: str = "PAYMENT") -> None:
        if not self.evidence_id or not self.issuer:
            raise AuthorizationError("authorization evidence is incomplete")
        if self.agent_id != agent_id or self.account_id != account_id:
            raise AuthorizationError("authorization subject/account mismatch")
        if self.scope and action not in self.scope:
            raise AuthorizationError("requested action is outside authorization scope")
        if self.max_amount is not None and amount > self.max_amount:
            raise AuthorizationError("payment exceeds authorized amount")
        if self.currency is not None and self.currency.upper() != currency.upper():
            raise AuthorizationError("payment currency is outside authorization")
        if self.valid_until is not None:
            expiry = self.valid_until
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) >= expiry:
                raise AuthorizationError("authorization evidence is expired")
