from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ProviderOutcome(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN_EXTERNAL_OUTCOME"


class PaymentProvider:
    def charge(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str) -> ProviderOutcome:
        raise NotImplementedError

    def capture(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str) -> ProviderOutcome:
        raise NotImplementedError

    def void(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str) -> ProviderOutcome:
        raise NotImplementedError

    def refund(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str) -> ProviderOutcome:
        raise NotImplementedError


@dataclass
class MockProvider(PaymentProvider):
    outcome: ProviderOutcome = ProviderOutcome.SUCCEEDED
    calls: int = 0
    _results: dict[str, ProviderOutcome] = field(default_factory=dict)

    def _run(self, idempotency_key: str) -> ProviderOutcome:
        if idempotency_key in self._results:
            return self._results[idempotency_key]
        self.calls += 1
        self._results[idempotency_key] = self.outcome
        return self.outcome

    def charge(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str) -> ProviderOutcome:
        return self._run(idempotency_key)

    def capture(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str) -> ProviderOutcome:
        return self._run(idempotency_key)

    def void(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str) -> ProviderOutcome:
        return self._run(idempotency_key)

    def refund(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str) -> ProviderOutcome:
        return self._run(idempotency_key)
