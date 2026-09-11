from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class PaymentStatus(StrEnum):
    REQUESTED = "REQUESTED"
    POLICY_CHECK = "POLICY_CHECK"
    BUDGET_CHECK = "BUDGET_CHECK"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVED = "APPROVED"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    AUTHENTICATED = "AUTHENTICATED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PROCESSING = "PROCESSING"
    UNKNOWN_EXTERNAL_OUTCOME = "UNKNOWN_EXTERNAL_OUTCOME"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Decision(StrEnum):
    ALLOW_AUTO = "ALLOW_AUTO"
    ALLOW_NOTIFY = "ALLOW_NOTIFY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    DENY = "DENY"


@dataclass(frozen=True)
class Money:
    value: Decimal
    currency: str

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("money value cannot be negative")
        if len(self.currency) != 3:
            raise ValueError("currency must be ISO-4217 style 3-letter code")


@dataclass(frozen=True)
class PaymentIntent:
    payment_id: str
    agent_id: str
    amount: Money
    merchant_domain: str
    idempotency_key: str

    def fingerprint(self) -> tuple[str, str, Decimal, str, str]:
        return (
            self.agent_id,
            self.merchant_domain,
            self.amount.value,
            self.amount.currency,
            self.payment_id,
        )
