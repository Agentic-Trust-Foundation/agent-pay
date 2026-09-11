"""Deterministic V1 spending-policy evaluation."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .domain import Decision, PaymentIntent


@dataclass(frozen=True)
class SpendingPolicy:
    per_transaction_limit: Decimal
    notify_above: Decimal | None = None
    approval_above: Decimal | None = None
    allowed_categories: frozenset[str] | None = None
    denied_categories: frozenset[str] = frozenset()
    allowed_domains: frozenset[str] | None = None
    denied_domains: frozenset[str] = frozenset()

    def evaluate(self, intent: PaymentIntent, *, category: str | None = None) -> Decision:
        amount = intent.amount.value
        if amount > self.per_transaction_limit:
            return Decision.DENY
        if category and category in self.denied_categories:
            return Decision.DENY
        if self.allowed_categories is not None and category not in self.allowed_categories:
            return Decision.DENY
        if intent.merchant_domain in self.denied_domains:
            return Decision.DENY
        if self.allowed_domains is not None and intent.merchant_domain not in self.allowed_domains:
            return Decision.DENY
        if self.approval_above is not None and amount > self.approval_above:
            return Decision.REQUIRE_APPROVAL
        if self.notify_above is not None and amount > self.notify_above:
            return Decision.ALLOW_NOTIFY
        return Decision.ALLOW_AUTO

    @classmethod
    def from_rules(cls, rules: dict[str, Any]) -> "SpendingPolicy":
        limits = rules.get("limits", {})
        merchant = rules.get("merchant", {})
        categories = rules.get("categories", {})
        return cls(
            per_transaction_limit=Decimal(str(limits.get("per_transaction", "0"))),
            notify_above=_decimal_or_none(limits.get("notify_above")),
            approval_above=_decimal_or_none(limits.get("approval_above")),
            allowed_categories=frozenset(categories["allow"]) if "allow" in categories else None,
            denied_categories=frozenset(categories.get("deny", [])),
            allowed_domains=frozenset(merchant["allow_domains"]) if "allow_domains" in merchant else None,
            denied_domains=frozenset(merchant.get("deny_domains", [])),
        )


def _decimal_or_none(value: Any) -> Decimal | None:
    return None if value is None else Decimal(str(value))
