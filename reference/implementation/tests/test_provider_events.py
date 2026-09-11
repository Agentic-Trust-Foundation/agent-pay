import hashlib
import hmac

from agent_pay.provider_events import verify_hmac_signature


def test_provider_signature_verification():
    payload = b'{"id":"evt_1"}'
    secret = "test-secret"
    signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert verify_hmac_signature(payload, "sha256=" + signature, secret)
    assert not verify_hmac_signature(payload, "sha256=" + "0" * 64, secret)
