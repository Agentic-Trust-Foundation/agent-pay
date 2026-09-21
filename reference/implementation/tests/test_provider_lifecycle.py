from agent_pay.provider import MockProvider, ProviderOutcome


def test_capture_is_idempotent_at_provider_boundary():
    provider = MockProvider(ProviderOutcome.SUCCEEDED)
    first = provider.capture("pay-1", 1000, "USD", "payment:pay-1:capture")
    second = provider.capture("pay-1", 1000, "USD", "payment:pay-1:capture")
    assert first == second == ProviderOutcome.SUCCEEDED
    assert provider.calls == 1


def test_void_and_refund_have_independent_idempotency_keys():
    provider = MockProvider(ProviderOutcome.SUCCEEDED)
    provider.void("pay-1", 1000, "USD", "payment:pay-1:void")
    provider.refund("pay-1", 1000, "USD", "payment:pay-1:refund:r1")
    provider.refund("pay-1", 1000, "USD", "payment:pay-1:refund:r1")
    assert provider.calls == 2


def test_lifecycle_operations_preserve_unknown_outcome():
    provider = MockProvider(ProviderOutcome.UNKNOWN)
    assert provider.capture("pay-1", 1000, "USD", "payment:pay-1:capture") == ProviderOutcome.UNKNOWN
    assert provider.void("pay-1", 1000, "USD", "payment:pay-1:void") == ProviderOutcome.UNKNOWN
    assert provider.refund("pay-1", 1000, "USD", "payment:pay-1:refund:r1") == ProviderOutcome.UNKNOWN



def test_lifecycle_operation_amount_must_match_payment():
    from decimal import Decimal
    from agent_pay.lifecycle import PaymentLifecycle

    amount, currency = PaymentLifecycle._validate_operation_amount(
        requested_amount=Decimal("10.00"),
        requested_currency="usd",
        payment_amount=Decimal("10.00"),
        payment_currency="USD",
    )
    assert amount == Decimal("10.00")
    assert currency == "USD"

    import pytest
    with pytest.raises(ValueError, match="does not match payment amount"):
        PaymentLifecycle._validate_operation_amount(
            requested_amount=Decimal("9.99"),
            requested_currency="USD",
            payment_amount=Decimal("10.00"),
            payment_currency="USD",
        )

    with pytest.raises(ValueError, match="does not match payment currency"):
        PaymentLifecycle._validate_operation_amount(
            requested_amount=Decimal("10.00"),
            requested_currency="EUR",
            payment_amount=Decimal("10.00"),
            payment_currency="USD",
        )


def test_refund_amount_may_be_partial_but_currency_must_match():
    from decimal import Decimal
    from agent_pay.lifecycle import PaymentLifecycle
    import pytest

    amount, currency = PaymentLifecycle._validate_refund_amount(
        requested_amount=Decimal("6.00"),
        requested_currency="usd",
        payment_currency="USD",
    )
    assert amount == Decimal("6.00")
    assert currency == "USD"

    with pytest.raises(ValueError, match="does not match payment currency"):
        PaymentLifecycle._validate_refund_amount(
            requested_amount=Decimal("6.00"),
            requested_currency="EUR",
            payment_currency="USD",
        )
