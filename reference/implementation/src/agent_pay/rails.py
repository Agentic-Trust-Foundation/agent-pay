from __future__ import annotations

from dataclasses import dataclass, field

from .provider import PaymentProvider, ProviderOutcome


@dataclass
class SimulatedPaymentRail(PaymentProvider):
    """Deterministic reference rail used to exercise routing without real credentials."""

    name: str
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


class WalletRail(SimulatedPaymentRail):
    def __init__(self, outcome: ProviderOutcome = ProviderOutcome.SUCCEEDED) -> None:
        super().__init__(name="wallet", outcome=outcome)


class VirtualCardRail(SimulatedPaymentRail):
    def __init__(self, outcome: ProviderOutcome = ProviderOutcome.SUCCEEDED) -> None:
        super().__init__(name="virtual_card", outcome=outcome)
