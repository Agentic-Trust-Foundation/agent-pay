from decimal import Decimal

from agent_pay.provider import ProviderOutcome
from agent_pay.provider_events import verify_hmac_signature
from agent_pay.reconciliation import compare_amounts
from agent_pay.simulator import ProviderSimulator


def test_timeout_webhook_settlement_reconciliation():
    provider = ProviderSimulator()
    payment_id = "pay-e2e-001"

    # Agent-Pay cannot observe the provider's final result at request time.
    observed = provider.charge(payment_id, Decimal("25.00"), "usd", ProviderOutcome.UNKNOWN)
    assert observed == ProviderOutcome.UNKNOWN

    body, signature = provider.webhook(payment_id)
    assert verify_hmac_signature(body, signature, provider.secret)

    settlement = provider.settlement(payment_id)
    assert settlement["provider_reference"] in body.decode()

    status, code = compare_amounts(
        expected_amount=Decimal("25.00"),
        observed_amount=settlement["amount"],
        expected_currency="USD",
        observed_currency=settlement["currency"],
    )
    assert (status, code) == ("MATCHED", None)


def test_failed_operation_does_not_settle():
    provider = ProviderSimulator()
    payment_id = "pay-e2e-failed"

    observed = provider.charge(payment_id, Decimal("30.00"), "USD", ProviderOutcome.FAILED)
    assert observed == ProviderOutcome.FAILED

    try:
        provider.settlement(payment_id)
    except ValueError as exc:
        assert str(exc) == "failed provider operation cannot settle"
    else:
        raise AssertionError("failed provider operation unexpectedly settled")


def test_duplicate_charge_is_provider_idempotent():
    provider = ProviderSimulator()
    payment_id = "pay-e2e-idempotent"

    first = provider.charge(payment_id, Decimal("10.00"), "USD", ProviderOutcome.UNKNOWN)
    second = provider.charge(payment_id, Decimal("10.00"), "USD", ProviderOutcome.UNKNOWN)

    assert first == second == ProviderOutcome.UNKNOWN
    assert len(provider.operations) == 1
