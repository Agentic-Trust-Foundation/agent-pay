from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256


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
    _references: dict[str, str] = field(default_factory=dict)

    def _run(self, idempotency_key: str) -> ProviderOutcome:
        if idempotency_key in self._results:
            return self._results[idempotency_key]
        self.calls += 1
        self._results[idempotency_key] = self.outcome
        self._references[idempotency_key] = f"mock-{sha256(idempotency_key.encode()).hexdigest()[:16]}"
        return self.outcome

    def reference_for(self, idempotency_key: str) -> str | None:
        return self._references.get(idempotency_key)

    def charge(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str) -> ProviderOutcome:
        return self._run(idempotency_key)

    def capture(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str) -> ProviderOutcome:
        return self._run(idempotency_key)

    def void(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str) -> ProviderOutcome:
        return self._run(idempotency_key)

    def refund(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str) -> ProviderOutcome:
        return self._run(idempotency_key)


@dataclass
class SandboxProvider(PaymentProvider):
    """Deterministic provider sandbox for Phase 3 conformance.

    It models success/failure/unknown outcomes and stable provider references
    without making network calls or claiming a live PSP integration.
    """

    default_outcome: ProviderOutcome = ProviderOutcome.SUCCEEDED
    calls: int = 0
    _results: dict[str, ProviderOutcome] = field(default_factory=dict)
    _references: dict[str, str] = field(default_factory=dict)
    _planned: dict[str, ProviderOutcome] = field(default_factory=dict)

    def plan(self, idempotency_key: str, outcome: ProviderOutcome) -> None:
        self._planned[idempotency_key] = outcome

    def _run(self, idempotency_key: str) -> ProviderOutcome:
        if idempotency_key in self._results:
            return self._results[idempotency_key]
        self.calls += 1
        outcome = self._planned.get(idempotency_key, self.default_outcome)
        self._results[idempotency_key] = outcome
        self._references[idempotency_key] = (
            f"sandbox-{sha256(idempotency_key.encode()).hexdigest()[:16]}"
        )
        return outcome

    def reference_for(self, idempotency_key: str) -> str | None:
        return self._references.get(idempotency_key)

    def charge(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str) -> ProviderOutcome:
        return self._run(idempotency_key)

    def capture(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str) -> ProviderOutcome:
        return self._run(idempotency_key)

    def void(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str) -> ProviderOutcome:
        return self._run(idempotency_key)

    def refund(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str) -> ProviderOutcome:
        return self._run(idempotency_key)
