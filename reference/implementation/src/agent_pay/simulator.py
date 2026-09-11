"""Deterministic provider simulator for Agent-Pay end-to-end tests.

The simulator models the failure boundary that matters most for payments:
the provider may accept a charge while the caller sees a timeout. The final
truth is then delivered through a signed webhook, followed by settlement.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from decimal import Decimal

from .provider import ProviderOutcome


@dataclass
class SimulatedOperation:
    operation_id: str
    payment_id: str
    amount: Decimal
    currency: str
    outcome: ProviderOutcome
    provider_reference: str
    settled: bool = False


@dataclass
class ProviderSimulator:
    secret: str = "simulator-secret"
    operations: dict[str, SimulatedOperation] = field(default_factory=dict)
    _counter: int = 0

    def charge(self, payment_id: str, amount: Decimal, currency: str,
               outcome: ProviderOutcome = ProviderOutcome.UNKNOWN) -> ProviderOutcome:
        key = f"charge:{payment_id}"
        existing = self.operations.get(key)
        if existing:
            return existing.outcome
        self._counter += 1
        reference = f"sim_ch_{self._counter:06d}"
        # UNKNOWN represents the caller timing out even though the provider
        # operation has a deterministic final outcome available for webhook delivery.
        final_outcome = ProviderOutcome.SUCCEEDED if outcome == ProviderOutcome.UNKNOWN else outcome
        self.operations[key] = SimulatedOperation(
            operation_id=key,
            payment_id=payment_id,
            amount=Decimal(str(amount)),
            currency=currency.upper(),
            outcome=final_outcome,
            provider_reference=reference,
        )
        return ProviderOutcome.UNKNOWN if outcome == ProviderOutcome.UNKNOWN else outcome

    def webhook(self, payment_id: str) -> tuple[bytes, str]:
        operation = self.operations[f"charge:{payment_id}"]
        payload = {
            "event_id": f"evt_{operation.provider_reference}",
            "event_type": "payment.succeeded" if operation.outcome == ProviderOutcome.SUCCEEDED else "payment.failed",
            "payment_id": payment_id,
            "provider_reference": operation.provider_reference,
            "amount": str(operation.amount),
            "currency": operation.currency,
        }
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        signature = hmac.new(self.secret.encode(), body, hashlib.sha256).hexdigest()
        return body, f"sha256={signature}"

    def settlement(self, payment_id: str) -> dict:
        operation = self.operations[f"charge:{payment_id}"]
        if operation.outcome != ProviderOutcome.SUCCEEDED:
            raise ValueError("failed provider operation cannot settle")
        operation.settled = True
        return {
            "settlement_reference": f"set_{operation.provider_reference}",
            "provider_reference": operation.provider_reference,
            "amount": str(operation.amount),
            "currency": operation.currency,
        }
