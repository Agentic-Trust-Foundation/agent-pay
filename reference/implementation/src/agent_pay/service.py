from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .budget import Budget
from .domain import Decision, PaymentIntent, PaymentStatus
from .policy import SpendingPolicy
from .provider import PaymentProvider, ProviderOutcome


@dataclass
class PaymentResult:
    payment_id: str
    status: PaymentStatus
    decision: Decision


class PaymentService:
    def __init__(self, policy: SpendingPolicy, budget: Budget, provider: PaymentProvider):
        self.policy = policy
        self.budget = budget
        self.provider = provider
        self._idempotency: dict[str, tuple[tuple, PaymentResult]] = {}

    def create_payment(self, intent: PaymentIntent) -> PaymentResult:
        previous = self._idempotency.get(intent.idempotency_key)
        fingerprint = intent.fingerprint()
        if previous:
            old_fingerprint, result = previous
            if old_fingerprint != fingerprint:
                raise ValueError("idempotency key conflict")
            return result

        decision = self.policy.evaluate(intent)
        if decision == Decision.DENY:
            result = PaymentResult(intent.payment_id, PaymentStatus.FAILED, decision)
        elif decision == Decision.REQUIRE_APPROVAL:
            result = PaymentResult(intent.payment_id, PaymentStatus.APPROVAL_REQUIRED, decision)
        else:
            if not self.budget.reserve(intent.amount.value):
                result = PaymentResult(intent.payment_id, PaymentStatus.FAILED, Decision.DENY)
            else:
                result = self._execute(intent, decision)
        self._idempotency[intent.idempotency_key] = (fingerprint, result)
        return result

    def _execute(self, intent: PaymentIntent, decision: Decision) -> PaymentResult:
        provider = self.provider
        selector = getattr(provider, "for_payment", None)
        if selector is not None:
            provider = selector(intent.merchant_domain, intent.amount.currency)

        provider_key = f"payment:{intent.payment_id}:charge"
        outcome = provider.charge(
            intent.payment_id,
            int(intent.amount.value * Decimal("100")),
            intent.amount.currency,
            provider_key,
        )
        if outcome == ProviderOutcome.SUCCEEDED:
            self.budget.consume(intent.amount.value)
            return PaymentResult(intent.payment_id, PaymentStatus.SUCCEEDED, decision)
        if outcome == ProviderOutcome.FAILED:
            self.budget.release(intent.amount.value)
            return PaymentResult(intent.payment_id, PaymentStatus.FAILED, decision)
        return PaymentResult(intent.payment_id, PaymentStatus.UNKNOWN_EXTERNAL_OUTCOME, decision)
