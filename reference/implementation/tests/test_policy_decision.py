from datetime import datetime
from decimal import Decimal

from agent_pay.domain import Decision, Money, PaymentIntent
from agent_pay.policy import SpendingPolicy


def intent(amount="50", currency="USD", domain="shop.example"):
    return PaymentIntent("pay-1", "agent-1", Money(Decimal(amount), currency), domain, "req-1")


def test_policy_decision_contains_auditable_evidence():
    policy = SpendingPolicy.from_rules({
        "limits": {"per_transaction": "300", "approval_above": "100"},
        "currency": {"allow": ["USD", "EUR"]},
    })
    result = policy.evaluate_with_trace(intent("150"), policy_version="pv-1:v2")
    assert result.decision == Decision.REQUIRE_APPROVAL
    assert result.policy_version == "pv-1:v2"
    assert "AMOUNT_REQUIRES_APPROVAL" in result.reasons
    assert result.evidence()["decision"] == "REQUIRE_APPROVAL"


def test_policy_denies_currency_outside_allowlist():
    policy = SpendingPolicy.from_rules({
        "limits": {"per_transaction": "300"},
        "currency": {"allow": ["USD"]},
    })
    result = policy.evaluate_with_trace(intent("10", "EUR"))
    assert result.decision == Decision.DENY
    assert "CURRENCY_NOT_ALLOWED" in result.reasons


def test_policy_missing_limit_fails_closed():
    result = SpendingPolicy.from_rules({}).evaluate_with_trace(intent("1"))
    assert result.decision == Decision.DENY
    assert "POLICY_LIMIT_NOT_CONFIGURED" in result.reasons


def test_policy_multidimensional_context_normalizes_and_denies():
    policy = SpendingPolicy.from_rules({
        "limits": {"per_transaction": "300"},
        "merchant": {"allow_domains": ["shop.example"]},
        "categories": {"allow": ["software"]},
        "region": {"allow": ["EU"], "deny": ["KP"]},
        "instrument": {"allow": ["virtual_card"]},
        "schedule": {"allow_weekdays": [0, 1, 2, 3, 4], "start_time": "09:00", "end_time": "18:00"},
    })
    result = policy.evaluate_with_trace(
        PaymentIntent(
            "pay-2", "agent-1", Money(Decimal("20"), "usd"),
            " SHOP.EXAMPLE ", "req-2",
            merchant_category="Software",
            region="eu",
            instrument_class="VIRTUAL_CARD",
            requested_at=datetime(2026, 9, 21, 12, 30),
        )
    )
    assert result.decision == Decision.ALLOW_AUTO

    denied = policy.evaluate_with_trace(
        PaymentIntent(
            "pay-3", "agent-1", Money(Decimal("20"), "USD"),
            "shop.example", "req-3",
            merchant_category="software",
            region="EU",
            instrument_class="virtual_card",
            requested_at=datetime(2026, 9, 21, 20, 0),
        )
    )
    assert denied.decision == Decision.DENY
    assert "TIME_WINDOW_NOT_ALLOWED" in denied.reasons


def test_policy_missing_required_time_context_fails_closed():
    policy = SpendingPolicy.from_rules({
        "limits": {"per_transaction": "300"},
        "schedule": {"allow_weekdays": [0, 1, 2, 3, 4]},
    })
    result = policy.evaluate_with_trace(intent("10"))
    assert result.decision == Decision.DENY
    assert "REQUEST_TIME_REQUIRED" in result.reasons


def test_policy_cross_midnight_window_is_deterministic():
    policy = SpendingPolicy.from_rules({
        "limits": {"per_transaction": "300"},
        "schedule": {"start_time": "22:00", "end_time": "02:00"},
    })
    assert policy.evaluate_with_trace(
        PaymentIntent("pay-4", "agent-1", Money(Decimal("10"), "USD"), "shop.example", "req-4",
                      requested_at=datetime(2026, 9, 21, 23, 30))
    ).decision == Decision.ALLOW_AUTO
    assert policy.evaluate_with_trace(
        PaymentIntent("pay-5", "agent-1", Money(Decimal("10"), "USD"), "shop.example", "req-5",
                      requested_at=datetime(2026, 9, 21, 12, 0))
    ).decision == Decision.DENY


def test_policy_invalid_schedule_fails_before_evaluation():
    import pytest
    with pytest.raises(ValueError, match="invalid policy schedule"):
        SpendingPolicy.from_rules({
            "limits": {"per_transaction": "300"},
            "schedule": {"allow_weekdays": [7]},
        })
