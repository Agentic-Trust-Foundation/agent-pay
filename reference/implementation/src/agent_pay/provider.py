from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ProviderOutcome(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN_EXTERNAL_OUTCOME"


class PaymentProvider:
    def charge(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str) -> ProviderOutcome:
        raise NotImplementedError


@dataclass
class MockProvider(PaymentProvider):
    outcome: ProviderOutcome = ProviderOutcome.SUCCEEDED
    calls: int = 0

    def charge(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str) -> ProviderOutcome:
        self.calls += 1
        return self.outcome
