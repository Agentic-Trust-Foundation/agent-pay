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
