"""Provider webhook ingestion with deduplication and secret redaction."""

import hashlib
import hmac
import json


_SECRET_KEYS = {
    "pan", "card_number", "cvv", "cvc", "pin", "private_key",
    "secret", "api_key", "access_token", "refresh_token", "authorization",
}


def sanitize_payload(value):
    if isinstance(value, dict):
        return {
            str(k): "[REDACTED]" if str(k).lower() in _SECRET_KEYS
            else sanitize_payload(v)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [sanitize_payload(v) for v in value]
    return value


class ProviderEventRepository:
    def __init__(self, conn):
        self.conn = conn

    def record(self, *, provider_name: str, event_id: str, event_type: str,
               payload: dict, signature_valid: bool):
        safe_payload = sanitize_payload(payload)
        encoded = json.dumps(safe_payload, sort_keys=True, separators=(",", ":")).encode()
        digest = hashlib.sha256(encoded).hexdigest()
        row = self.conn.execute(
            """INSERT INTO provider_events
               (provider_name, provider_event_id, event_type, signature_valid,
                payload, payload_digest)
               VALUES (%s,%s,%s,%s,%s::jsonb,%s)
               ON CONFLICT (provider_name, provider_event_id) DO NOTHING
               RETURNING id""",
            (provider_name, event_id, event_type, signature_valid,
             json.dumps(safe_payload), digest),
        ).fetchone()
        return row[0] if row else None


def verify_hmac_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    supplied = signature.removeprefix("sha256=")
    return hmac.compare_digest(expected, supplied)


def mark_processed(conn, event_id) -> None:
    conn.execute(
        "UPDATE provider_events SET processing_status='PROCESSED', processed_at=now() WHERE id=%s",
        (event_id,),
    )
