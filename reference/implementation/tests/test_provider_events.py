import hashlib
import hmac

from agent_pay.provider_events import sanitize_payload, verify_hmac_signature


def test_provider_signature_verification():
    payload = b'{"id":"evt_1"}'
    secret = "test-secret"
    signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert verify_hmac_signature(payload, "sha256=" + signature, secret)
    assert not verify_hmac_signature(payload, "sha256=" + "0" * 64, secret)


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


def test_hmac_signature_and_replay_window_helpers():
    import hashlib
    import hmac
    from agent_pay.provider_events import verify_hmac_signature
    body = b'{"event_id":"evt-1"}'
    secret = "phase21-secret"
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_hmac_signature(body, "sha256=" + sig, secret)
    assert not verify_hmac_signature(body, "sha256=" + ("0" * 64), secret)
