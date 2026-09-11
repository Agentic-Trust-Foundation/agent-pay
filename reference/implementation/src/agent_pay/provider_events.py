"""Provider webhook ingestion and durable event deduplication."""
import hashlib
import hmac
import json
from uuid import UUID


class ProviderEventRepository:
    def __init__(self, conn):
        self.conn = conn

    def record(self, *, provider_name: str, event_id: str, event_type: str,
               payload: dict, signature_valid: bool):
        row = self.conn.execute(
            """INSERT INTO provider_events
               (provider_name, provider_event_id, event_type, signature_valid, payload)
               VALUES (%s,%s,%s,%s,%s::jsonb)
               ON CONFLICT (provider_name, provider_event_id) DO NOTHING
               RETURNING id""",
            (provider_name, event_id, event_type, signature_valid, json.dumps(payload)),
        ).fetchone()
        return row[0] if row else None


def verify_hmac_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    supplied = signature.removeprefix("sha256=")
    return hmac.compare_digest(expected, supplied)


def mark_processed(conn, event_id: UUID) -> None:
    conn.execute(
        "UPDATE provider_events SET processing_status='PROCESSED', processed_at=now() WHERE id=%s",
        (event_id,),
    )
