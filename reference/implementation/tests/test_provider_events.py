import hashlib
import hmac

from agent_pay.provider_events import verify_hmac_signature


def test_provider_signature_verification():
    payload = b'{"id":"evt_1"}'
    secret = "test-secret"
    signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert verify_hmac_signature(payload, "sha256=" + signature, secret)
    assert not verify_hmac_signature(payload, "sha256=" + "0" * 64, secret)


from agent_pay.provider_events import sanitize_payload


def test_provider_payload_redacts_primary_credentials():
    payload = {
        "card": {"pan": "4111111111111111", "cvv": "123"},
        "authorization": "Bearer secret",
        "safe": "value",
    }
    safe = sanitize_payload(payload)
    assert safe["card"]["pan"] == "[REDACTED]"
    assert safe["card"]["cvv"] == "[REDACTED]"
    assert safe["authorization"] == "[REDACTED]"
    assert safe["safe"] == "value"
