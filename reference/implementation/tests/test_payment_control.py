from decimal import Decimal

import pytest

from agent_pay.budget import Budget
from agent_pay.domain import Decision, Money, PaymentIntent, PaymentStatus
from agent_pay.policy import SpendingPolicy
from agent_pay.provider import MockProvider, ProviderOutcome
from agent_pay.service import PaymentService


def intent(payment_id="pay_1", key="key_1", amount="50"):
    return PaymentIntent(payment_id=payment_id, agent_id="agt_1", amount=Money(Decimal(amount), "USD"), merchant_domain="example.com", idempotency_key=key)


def service(provider=ProviderOutcome.SUCCEEDED):
    return PaymentService(
        SpendingPolicy(Decimal("500"), notify_above=Decimal("20"), approval_above=Decimal("100")),
        Budget(Decimal("1000")), MockProvider(provider),
    )


def test_policy_requires_approval_above_threshold():
    result = service().create_payment(intent(amount="150"))
    assert result.status == PaymentStatus.APPROVAL_REQUIRED


def test_success_consumes_budget():
    s = service(); result = s.create_payment(intent(amount="50"))
    assert result.status == PaymentStatus.SUCCEEDED
    assert s.budget.consumed == Decimal("50")
    assert s.budget.reserved == Decimal("0")


def test_provider_timeout_is_unknown_not_failed():
    s = service(ProviderOutcome.UNKNOWN); result = s.create_payment(intent(amount="50"))
    assert result.status == PaymentStatus.UNKNOWN_EXTERNAL_OUTCOME
    assert s.budget.reserved == Decimal("50")
    assert s.budget.consumed == Decimal("0")


def test_idempotent_replay_returns_same_result():
    s = service(); first = s.create_payment(intent(amount="50")); second = s.create_payment(intent(amount="50"))
    assert second == first
    assert s.budget.consumed == Decimal("50")


def test_idempotency_key_conflict_is_rejected():
    s = service(); s.create_payment(intent(amount="50"))
    with pytest.raises(ValueError, match="idempotency key conflict"):
        s.create_payment(intent(payment_id="pay_2", amount="60"))


def test_failed_provider_releases_reservation():
    s = service(ProviderOutcome.FAILED); result = s.create_payment(intent(amount="75"))
    assert result.status == PaymentStatus.FAILED
    assert s.budget.reserved == Decimal("0")
    assert s.budget.consumed == Decimal("0")


def test_budget_reservation_prevents_overspend():
    budget = Budget(Decimal("100"))
    assert budget.reserve(Decimal("70"))
    assert not budget.reserve(Decimal("40"))
    assert budget.available == Decimal("30")


def test_provider_idempotency_replays_without_second_charge():
    provider = MockProvider()
    assert provider.charge("pay_1", 5000, "USD", "payment:pay_1:charge") == ProviderOutcome.SUCCEEDED
    assert provider.charge("pay_1", 5000, "USD", "payment:pay_1:charge") == ProviderOutcome.SUCCEEDED
    assert provider.calls == 1
