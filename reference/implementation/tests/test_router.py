from decimal import Decimal

import pytest

from agent_pay.budget import Budget
from agent_pay.domain import Decision, Money, PaymentIntent, PaymentStatus
from agent_pay.policy import SpendingPolicy
from agent_pay.provider import MockProvider, ProviderOutcome
from agent_pay.rails import VirtualCardRail, WalletRail
from agent_pay.router import PaymentRouter, ProviderRoutingError
from agent_pay.service import PaymentService


def intent(payment_id: str, domain: str, currency: str = "USD") -> PaymentIntent:
    return PaymentIntent(
        payment_id=payment_id,
        agent_id="agent-1",
        amount=Money(Decimal("10"), currency),
        merchant_domain=domain,
        idempotency_key=f"idem-{payment_id}",
    )


def test_router_selects_first_matching_specific_route() -> None:
    router = PaymentRouter()
    wallet = WalletRail()
    card = VirtualCardRail()
    router.register("wallet-us", wallet, merchant_domains={"wallet.example"}, currencies={"USD"})
    router.register("card-default", card)

    assert router.provider_id_for("wallet.example", "USD") == "wallet-us"
    assert router.for_payment("wallet.example", "USD") is wallet
    assert router.provider_id_for("other.example", "EUR") == "card-default"
    assert router.for_payment("other.example", "EUR") is card


def test_router_rejects_unroutable_payment() -> None:
    router = PaymentRouter()
    router.register("wallet-us", WalletRail(), currencies={"USD"})
    with pytest.raises(ProviderRoutingError):
        router.for_payment("shop.example", "EUR")


def test_payment_service_uses_router_selected_rail() -> None:
    router = PaymentRouter()
    wallet = WalletRail()
    card = VirtualCardRail()
    router.register("wallet", wallet, merchant_domains={"wallet.example"})
    router.register("card", card)

    service = PaymentService(
        SpendingPolicy(max_amount=Decimal("100")),
        Budget(Decimal("100")),
        router,
    )

    result = service.create_payment(intent("p-wallet", "wallet.example"))
    assert result.status == PaymentStatus.SUCCEEDED
    assert result.decision == Decision.ALLOW_AUTO
    assert wallet.calls == 1
    assert card.calls == 0


def test_router_keeps_provider_idempotency() -> None:
    router = PaymentRouter()
    provider = MockProvider(outcome=ProviderOutcome.SUCCEEDED)
    router.register("mock", provider)
    selected = router.for_payment("shop.example", "USD")
    assert selected.charge("p1", 1000, "USD", "same-key") == ProviderOutcome.SUCCEEDED
    assert selected.charge("p1", 1000, "USD", "same-key") == ProviderOutcome.SUCCEEDED
    assert provider.calls == 1
