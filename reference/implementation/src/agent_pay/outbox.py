from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from uuid import UUID


@dataclass(frozen=True)
class OutboxEvent:
    event_id: str
    event_type: str
    aggregate_id: str
    payload: dict
    created_at: datetime


class InMemoryOutbox:
    """Reference semantics for an outbox; persistence belongs to PostgreSQL."""
    def __init__(self) -> None:
        self.events: dict[str, OutboxEvent] = {}

    def append(self, event: OutboxEvent) -> None:
        existing = self.events.get(event.event_id)
        if existing is not None and existing != event:
            raise ValueError("outbox event id conflict")
        self.events[event.event_id] = event

    def pending(self) -> list[OutboxEvent]:
        return list(self.events.values())


def new_event(event_id: str, event_type: str, aggregate_id: str, payload: dict) -> OutboxEvent:
    return OutboxEvent(event_id, event_type, aggregate_id, payload, datetime.now(timezone.utc))


def enqueue(conn, *, event_type: str, aggregate_type: str, aggregate_id: UUID,
             payload: dict, correlation_id: str | None = None) -> UUID:
    return conn.execute(
        """INSERT INTO outbox_events
           (event_type, aggregate_type, aggregate_id, payload, correlation_id)
           VALUES (%s, %s, %s, %s::jsonb, %s) RETURNING id""",
        (event_type, aggregate_type, aggregate_id, json.dumps(payload), correlation_id),
    ).fetchone()[0]


def claim_batch(conn, limit: int = 50):
    """Claim pending events for one publisher using row locks.

    The claim is intentionally short-lived. Publication happens outside the
    database transaction; callers must call mark_published or mark_failed.
    """
    return conn.execute(
        """UPDATE outbox_events
           SET status='PROCESSING', attempts=attempts+1
           WHERE id IN (
               SELECT id FROM outbox_events
               WHERE status='PENDING' AND available_at <= now()
               ORDER BY created_at
               FOR UPDATE SKIP LOCKED
               LIMIT %s
           )
           RETURNING id, event_type, aggregate_type, aggregate_id, payload,
                     correlation_id, attempts""",
        (limit,),
    ).fetchall()


def mark_published(conn, event_id: UUID) -> None:
    conn.execute(
        """UPDATE outbox_events
           SET status='PUBLISHED', published_at=now()
           WHERE id=%s AND status='PROCESSING'""",
        (event_id,),
    )


def mark_failed(conn, event_id: UUID, *, retry_after_seconds: int = 30) -> None:
    """Return a failed publication to PENDING with deterministic backoff."""
    if retry_after_seconds < 0:
        raise ValueError("retry_after_seconds must be non-negative")
    conn.execute(
        """UPDATE outbox_events
           SET status='PENDING',
               available_at=now() + (%s * interval '1 second')
           WHERE id=%s AND status='PROCESSING'""",
        (retry_after_seconds, event_id),
    )
