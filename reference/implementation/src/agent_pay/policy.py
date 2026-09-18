"""Deterministic V1 spending-policy evaluation."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .domain import Decision, PaymentIntent


@dataclass(frozen=True)
class PolicyDecision:
    decision: Decision
    policy_version: str | None
    reasons: tuple[str, ...]
    evaluated_rules: tuple[str, ...]

    def evidence(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "policy_version": self.policy_version,
            "reasons": list(self.reasons),
            "evaluated_rules": list(self.evaluated_rules),
        }


@dataclass(frozen=True)
class SpendingPolicy:
    per_transaction_limit: Decimal
    notify_above: Decimal | None = None
    approval_above: Decimal | None = None
    allowed_categories: frozenset[str] | None = None
    denied_categories: frozenset[str] = frozenset()
    allowed_domains: frozenset[str] | None = None
    denied_domains: frozenset[str] = frozenset()
    allowed_currencies: frozenset[str] | None = None
    denied_currencies: frozenset[str] = frozenset()

    def evaluate(self, intent: PaymentIntent, *, category: str | None = None) -> Decision:
        return self.evaluate_with_trace(intent, category=category).decision

    def evaluate_with_trace(
        self,
        intent: PaymentIntent,
        *,
        category: str | None = None,
        policy_version: str | None = None,
    ) -> PolicyDecision:
        amount = intent.amount.value
        currency = intent.amount.currency.upper()
        reasons: list[str] = []
        rules: list[str] = []

        if self.per_transaction_limit <= 0:
            return PolicyDecision(Decision.DENY, policy_version, ("POLICY_LIMIT_NOT_CONFIGURED",), ("per_transaction_limit > 0",))
        rules.append(f"amount <= {self.per_transaction_limit}")
        if amount > self.per_transaction_limit:
            reasons.append("AMOUNT_EXCEEDS_TRANSACTION_LIMIT")

        rules.append(f"currency in {sorted(self.allowed_currencies) if self.allowed_currencies is not None else 'ANY'}")
        if currency in self.denied_currencies:
            reasons.append("CURRENCY_DENIED")
        if self.allowed_currencies is not None and currency not in self.allowed_currencies:
            reasons.append("CURRENCY_NOT_ALLOWED")

        if category and category in self.denied_categories:
            reasons.append("CATEGORY_DENIED")
        if self.allowed_categories is not None and category not in self.allowed_categories:
            reasons.append("CATEGORY_NOT_ALLOWED")

        if intent.merchant_domain in self.denied_domains:
            reasons.append("MERCHANT_DOMAIN_DENIED")
        if self.allowed_domains is not None and intent.merchant_domain not in self.allowed_domains:
            reasons.append("MERCHANT_DOMAIN_NOT_ALLOWED")

        if reasons:
            return PolicyDecision(Decision.DENY, policy_version, tuple(reasons), tuple(rules))

        if self.approval_above is not None and amount > self.approval_above:
            return PolicyDecision(Decision.REQUIRE_APPROVAL, policy_version,
                                  ("AMOUNT_REQUIRES_APPROVAL",), tuple(rules))
        if self.notify_above is not None and amount > self.notify_above:
            return PolicyDecision(Decision.ALLOW_NOTIFY, policy_version,
                                  ("AMOUNT_REQUIRES_NOTIFICATION",), tuple(rules))
        return PolicyDecision(Decision.ALLOW_AUTO, policy_version, ("POLICY_ALLOWED",), tuple(rules))

    @classmethod
    def from_rules(cls, rules: dict[str, Any]) -> "SpendingPolicy":
        limits = rules.get("limits", {})
        merchant = rules.get("merchant", {})
        categories = rules.get("categories", {})
        currency = rules.get("currency", {})
        return cls(
            per_transaction_limit=Decimal(str(limits.get("per_transaction", "0"))),
            notify_above=_decimal_or_none(limits.get("notify_above")),
            approval_above=_decimal_or_none(limits.get("approval_above")),
            allowed_categories=frozenset(categories["allow"]) if "allow" in categories else None,
            denied_categories=frozenset(categories.get("deny", [])),
            allowed_domains=frozenset(merchant["allow_domains"]) if "allow_domains" in merchant else None,
            denied_domains=frozenset(merchant.get("deny_domains", [])),
            allowed_currencies=frozenset(str(x).upper() for x in currency.get("allow", [])) if "allow" in currency else None,
            denied_currencies=frozenset(str(x).upper() for x in currency.get("deny", [])),
        )


def _decimal_or_none(value: Any) -> Decimal | None:
    return None if value is None else Decimal(str(value))
