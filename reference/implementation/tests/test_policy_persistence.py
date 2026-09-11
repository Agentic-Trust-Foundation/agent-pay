from decimal import Decimal

from agent_pay.domain import Decision, Money, PaymentIntent
from agent_pay.policy import SpendingPolicy


def intent(amount="80", domain="shop.example", payment_id="pay-1"):
    return PaymentIntent(payment_id, "agent-1", Money(Decimal(amount), "USD"), domain, "req-1")


def test_rules_build_policy_and_require_approval():
    policy = SpendingPolicy.from_rules({
        "limits": {"per_transaction": "300", "notify_above": "20", "approval_above": "100"},
    })
    assert policy.evaluate(intent("150")) == Decision.REQUIRE_APPROVAL
    assert policy.evaluate(intent("50")) == Decision.ALLOW_NOTIFY
    assert policy.evaluate(intent("10")) == Decision.ALLOW_AUTO


def test_rules_deny_category_and_domain():
    policy = SpendingPolicy.from_rules({
        "limits": {"per_transaction": "300"},
        "categories": {"allow": ["food"], "deny": ["gambling"]},
        "merchant": {"deny_domains": ["blocked.example"]},
    })
    assert policy.evaluate(intent("10"), category="gambling") == Decision.DENY
    assert policy.evaluate(intent("10", domain="blocked.example"), category="food") == Decision.DENY
    assert policy.evaluate(intent("10"), category="electronics") == Decision.DENY


def test_rules_default_to_deny_when_no_transaction_limit():
    policy = SpendingPolicy.from_rules({})
    assert policy.evaluate(intent("1")) == Decision.DENY
