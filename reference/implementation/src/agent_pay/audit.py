"""Append-only audit and notification persistence helpers."""

from __future__ import annotations

import hashlib
import json


def _digest(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def record_audit(
    conn, *, event_id, account_id, actor_type, actor_reference, action,
    resource_type, resource_id, result, correlation_id, metadata
):
    row = conn.execute(
        """INSERT INTO audit_events
           (event_id, account_id, actor_type, actor_reference, action,
            resource_type, resource_id, result, correlation_id, metadata,
            immutable_digest)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)
           ON CONFLICT (event_id) DO NOTHING
           RETURNING id""",
        (
            event_id, account_id, actor_type, actor_reference, action,
            resource_type, resource_id, result, correlation_id,
            json.dumps(metadata), _digest(metadata),
        ),
    ).fetchone()
    if row:
        return row[0]
    return conn.execute(
        "SELECT id FROM audit_events WHERE event_id=%s", (event_id,)
    ).fetchone()[0]


def enqueue_notification(
    conn, *, event_id, account_id, notification_type, title, payload
):
    row = conn.execute(
        """INSERT INTO notifications
           (account_id, type, title, payload, source_event_id)
           VALUES (%s,%s,%s,%s::jsonb,%s)
           ON CONFLICT (source_event_id) DO NOTHING
           RETURNING id""",
        (account_id, notification_type, title, json.dumps(payload), event_id),
    ).fetchone()
    if row:
        return row[0]
    return conn.execute(
        "SELECT id FROM notifications WHERE source_event_id=%s",
        (event_id,),
    ).fetchone()[0]
