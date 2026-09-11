from dataclasses import dataclass
from decimal import Decimal

from .domain import Decision, PaymentIntent


@dataclass(frozen=True)
class SpendingPolicy:
    per_transaction_limit: Decimal
    notify_above: Decimal | None = None
    approval_above: Decimal | None = None

    def evaluate(self, intent: PaymentIntent) -> Decision:
        amount = intent.amount.value
        if amount > self.per_transaction_limit:
            return Decision.DENY
        if self.approval_above is not None and amount > self.approval_above:
            return Decision.REQUIRE_APPROVAL
        if self.notify_above is not None and amount > self.notify_above:
            return Decision.ALLOW_NOTIFY
        return Decision.ALLOW_AUTO
