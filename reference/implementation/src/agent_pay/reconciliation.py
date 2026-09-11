"""Provider settlement and reconciliation primitives."""
from decimal import Decimal


def compare_amounts(*, expected_amount, observed_amount, expected_currency: str, observed_currency: str):
    expected = Decimal(str(expected_amount))
    observed = Decimal(str(observed_amount))
    currency_match = expected_currency.strip().upper() == observed_currency.strip().upper()
    amount_match = expected == observed
    if currency_match and amount_match:
        return "MATCHED", None
    if not currency_match:
        return "DISCREPANCY", "CURRENCY_MISMATCH"
    return "DISCREPANCY", "AMOUNT_MISMATCH"
