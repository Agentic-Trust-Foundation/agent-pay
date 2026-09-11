from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ProviderOutcome(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN_EXTERNAL_OUTCOME"


class PaymentProvider:
    def charge(self, payment_id: str, amount_minor: int, currency: str) -> ProviderOutcome:
        raise NotImplementedError


@dataclass
class MockProvider(PaymentProvider):
    outcome: ProviderOutcome = ProviderOutcome.SUCCEEDED

    def charge(self, payment_id: str, amount_minor: int, currency: str) -> ProviderOutcome:
        return self.outcome
