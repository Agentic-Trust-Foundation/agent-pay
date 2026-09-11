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
