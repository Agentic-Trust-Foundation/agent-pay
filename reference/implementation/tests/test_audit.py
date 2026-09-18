from agent_pay.audit import _digest


def test_audit_digest_is_deterministic():
    assert _digest({"b": 2, "a": 1}) == _digest({"a": 1, "b": 2})
    assert _digest({"a": 1}) != _digest({"a": 2})


def test_audit_metadata_example_has_no_primary_credentials():
    payload = {"payment_id": "pay-1", "amount": "10", "currency": "USD"}
    assert "pan" not in payload
    assert "cvv" not in payload
    assert "private_key" not in payload
    assert "provider_secret" not in payload
