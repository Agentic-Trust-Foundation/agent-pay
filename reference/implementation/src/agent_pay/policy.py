"""Deterministic V1 spending-policy evaluation."""
from dataclasses import dataclass
from datetime import time
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
    allowed_regions: frozenset[str] | None = None
    denied_regions: frozenset[str] = frozenset()
    allowed_instrument_classes: frozenset[str] | None = None
    denied_instrument_classes: frozenset[str] = frozenset()
    allowed_weekdays: frozenset[int] | None = None
    start_time: time | None = None
    end_time: time | None = None

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
        currency = intent.amount.currency.strip().upper()
        domain = intent.merchant_domain.strip().lower()
        category = (category or intent.merchant_category or "").strip().lower() or None
        region = (intent.region or "").strip().upper() or None
        instrument_class = (intent.instrument_class or "").strip().lower() or None
        requested_at = intent.requested_at
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

        if domain in self.denied_domains:
            reasons.append("MERCHANT_DOMAIN_DENIED")
        if self.allowed_domains is not None and domain not in self.allowed_domains:
            reasons.append("MERCHANT_DOMAIN_NOT_ALLOWED")

        if region and region in self.denied_regions:
            reasons.append("REGION_DENIED")
        if self.allowed_regions is not None and region not in self.allowed_regions:
            reasons.append("REGION_NOT_ALLOWED")

        if instrument_class and instrument_class in self.denied_instrument_classes:
            reasons.append("INSTRUMENT_CLASS_DENIED")
        if self.allowed_instrument_classes is not None and instrument_class not in self.allowed_instrument_classes:
            reasons.append("INSTRUMENT_CLASS_NOT_ALLOWED")

        if self.allowed_weekdays is not None:
            if requested_at is None:
                reasons.append("REQUEST_TIME_REQUIRED")
            elif requested_at.weekday() not in self.allowed_weekdays:
                reasons.append("WEEKDAY_NOT_ALLOWED")

        if self.start_time is not None or self.end_time is not None:
            if requested_at is None:
                reasons.append("REQUEST_TIME_REQUIRED")
            elif not _time_in_window(requested_at.time(), self.start_time, self.end_time):
                reasons.append("TIME_WINDOW_NOT_ALLOWED")

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
        region = rules.get("region", {})
        instrument = rules.get("instrument", {})
        schedule = rules.get("schedule", {})
        try:
            allowed_weekdays = _parse_weekdays(schedule.get("allow_weekdays")) if "allow_weekdays" in schedule else None
            start_time = _parse_time(schedule.get("start_time")) if "start_time" in schedule else None
            end_time = _parse_time(schedule.get("end_time")) if "end_time" in schedule else None
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid policy schedule") from exc
        return cls(
            per_transaction_limit=Decimal(str(limits.get("per_transaction", "0"))),
            notify_above=_decimal_or_none(limits.get("notify_above")),
            approval_above=_decimal_or_none(limits.get("approval_above")),
            allowed_categories=frozenset(str(x).strip().lower() for x in categories["allow"]) if "allow" in categories else None,
            denied_categories=frozenset(str(x).strip().lower() for x in categories.get("deny", [])),
            allowed_domains=frozenset(str(x).strip().lower() for x in merchant["allow_domains"]) if "allow_domains" in merchant else None,
            denied_domains=frozenset(str(x).strip().lower() for x in merchant.get("deny_domains", [])),
            allowed_currencies=frozenset(str(x).upper() for x in currency.get("allow", [])) if "allow" in currency else None,
            denied_currencies=frozenset(str(x).upper() for x in currency.get("deny", [])),
            allowed_regions=frozenset(str(x).upper() for x in region["allow"]) if "allow" in region else None,
            denied_regions=frozenset(str(x).upper() for x in region.get("deny", [])),
            allowed_instrument_classes=frozenset(str(x).lower() for x in instrument["allow"]) if "allow" in instrument else None,
            denied_instrument_classes=frozenset(str(x).lower() for x in instrument.get("deny", [])),
            allowed_weekdays=allowed_weekdays,
            start_time=start_time,
            end_time=end_time,
        )


def _decimal_or_none(value: Any) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _parse_weekdays(value: Any) -> frozenset[int]:
    if not isinstance(value, (list, tuple, set)):
        raise ValueError("weekdays must be a list")
    result = frozenset(int(day) for day in value)
    if any(day < 0 or day > 6 for day in result):
        raise ValueError("weekday must be between 0 and 6")
    return result


def _parse_time(value: Any) -> time:
    if not isinstance(value, str):
        raise ValueError("time must be HH:MM")
    return time.fromisoformat(value)


def _time_in_window(value: time, start: time | None, end: time | None) -> bool:
    if start is None and end is None:
        return True
    if start is None:
        return value <= end
    if end is None:
        return value >= start
    if start <= end:
        return start <= value <= end
    return value >= start or value <= end
