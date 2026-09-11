from agent_pay.reconciliation import compare_amounts


def test_reconciliation_matches_amount_and_currency():
    assert compare_amounts(expected_amount="10.00", observed_amount="10.00", expected_currency="USD", observed_currency="USD") == ("MATCHED", None)


def test_reconciliation_detects_amount_mismatch():
    assert compare_amounts(expected_amount="10.00", observed_amount="11.00", expected_currency="USD", observed_currency="USD") == ("DISCREPANCY", "AMOUNT_MISMATCH")


def test_reconciliation_detects_currency_mismatch():
    assert compare_amounts(expected_amount="10.00", observed_amount="10.00", expected_currency="USD", observed_currency="EUR") == ("DISCREPANCY", "CURRENCY_MISMATCH")
