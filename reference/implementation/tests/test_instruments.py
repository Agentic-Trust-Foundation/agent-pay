import pytest

from agent_pay.instruments import (
    InstrumentEligibilityError,
    InstrumentSelector,
    InstrumentStatus,
    InstrumentType,
    PaymentInstrument,
)


def instrument(**overrides):
    values = {
        "instrument_id": "wallet-1",
        "account_id": "account-1",
        "instrument_type": InstrumentType.WALLET,
        "currency": "USD",
    }
    values.update(overrides)
    return PaymentInstrument(**values)


def test_selects_first_eligible_in_deterministic_order():
    selector = InstrumentSelector([
        instrument(instrument_id="suspended", status=InstrumentStatus.SUSPENDED),
        instrument(instrument_id="wallet-2"),
    ])
    assert selector.select(account_id="account-1", currency="USD").instrument_id == "wallet-2"


def test_rejects_cross_account_instrument():
    selector = InstrumentSelector([instrument(account_id="other")])
    with pytest.raises(InstrumentEligibilityError, match="different account"):
        selector.select(account_id="account-1", currency="USD")


def test_rejects_currency_mismatch():
    selector = InstrumentSelector([instrument(currency="EUR")])
    with pytest.raises(InstrumentEligibilityError, match="currency"):
        selector.select(account_id="account-1", currency="USD")


def test_rejects_closed_instrument():
    selector = InstrumentSelector([instrument(status=InstrumentStatus.CLOSED)])
    with pytest.raises(InstrumentEligibilityError, match="closed"):
        selector.select(account_id="account-1", currency="USD")


def test_merchant_constraint_is_enforced():
    selector = InstrumentSelector([
        instrument(merchant_domains=frozenset({"example.com"})),
    ])
    with pytest.raises(InstrumentEligibilityError, match="merchant"):
        selector.select(account_id="account-1", currency="USD", merchant_domain="other.example")


def test_provider_reference_is_opaque_metadata_only():
    selected = InstrumentSelector([
        instrument(provider_reference="opaque-provider-instrument-id"),
    ]).select(account_id="account-1", currency="USD")
    assert selected.provider_reference == "opaque-provider-instrument-id"
    assert not hasattr(selected, "pan")
    assert not hasattr(selected, "cvv")
