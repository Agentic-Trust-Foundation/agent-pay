from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


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
