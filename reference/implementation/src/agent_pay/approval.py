"""Approval state machine and immutable intent binding primitives."""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from decimal import Decimal


class ApprovalError(ValueError):
    """Raised when an approval cannot safely transition."""


@dataclass(frozen=True)
class ApprovalBinding:
    payment_request_id: str
    account_id: str
    agent_id: str
    amount: Decimal
    currency: str
    merchant_reference: str | None
    policy_version_id: str | None
    authorization_evidence_id: str | None

    def digest(self) -> str:
        payload = {
            "payment_request_id": self.payment_request_id,
            "account_id": self.account_id,
            "agent_id": self.agent_id,
            "amount": str(self.amount),
            "currency": self.currency.upper(),
            "merchant_reference": self.merchant_reference,
            "policy_version_id": self.policy_version_id,
            "authorization_evidence_id": self.authorization_evidence_id,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


def ensure_pending(*, status: str, expires_at: datetime | None) -> None:
    if status != "PENDING":
        raise ApprovalError("approval is no longer pending")
    if expires_at is not None:
        expiry = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) >= expiry:
            raise ApprovalError("approval has expired")
