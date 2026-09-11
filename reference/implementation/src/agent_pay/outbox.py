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
    return conn.execute(
        """SELECT id, event_type, aggregate_type, aggregate_id, payload
           FROM outbox_events
           WHERE status = 'PENDING' AND available_at <= now()
           ORDER BY created_at
           FOR UPDATE SKIP LOCKED
           LIMIT %s""",
        (limit,),
    ).fetchall()
