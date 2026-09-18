"""PostgreSQL outbox consumer for audit and notification side effects."""

from __future__ import annotations

from uuid import UUID

from .audit import enqueue_notification, record_audit
from .db import connection
from .outbox import claim_batch, mark_failed, mark_published
from .unit_of_work import UnitOfWork


AUDITABLE_EVENTS = {
    "PaymentRequested", "PaymentStarted", "PaymentSucceeded", "PaymentFailed",
    "PaymentOutcomeUnknown", "ApprovalRequested", "PaymentApproved",
    "PaymentDenied", "PaymentRefunded", "PaymentRefundRequested",
    "PaymentAuthenticationRequired", "PaymentAuthenticationCompleted",
    "BudgetReservationCreated", "BudgetReservationReleased", "BudgetConsumed",
}


def _account_for(conn, aggregate_type, aggregate_id):
    if aggregate_type == "payment":
        row = conn.execute(
            """SELECT pr.account_id
               FROM payments p JOIN payment_requests pr ON pr.id=p.payment_request_id
               WHERE p.id=%s""",
            (aggregate_id,),
        ).fetchone()
        return row[0] if row else None
    return None


def process_once(*, limit: int = 50) -> int:
    processed = 0
    with connection() as conn:
        with UnitOfWork(conn):
            claimed = claim_batch(conn, limit)

    for event_id, event_type, aggregate_type, aggregate_id, payload, correlation_id, attempts in claimed:
        try:
            with connection() as conn:
                with UnitOfWork(conn):
                    account_id = _account_for(conn, aggregate_type, aggregate_id)
                    if event_type in AUDITABLE_EVENTS:
                        record_audit(
                            conn, event_id=UUID(str(event_id)), account_id=account_id,
                            actor_type="SYSTEM", actor_reference="agent-pay-outbox",
                            action=event_type, resource_type=aggregate_type,
                            resource_id=aggregate_id, result="RECORDED",
                            correlation_id=correlation_id, metadata=payload or {},
                        )
                    if event_type == "NotificationRequested":
                        if not account_id:
                            raise ValueError("notification event has no account")
                        enqueue_notification(
                            conn, event_id=UUID(str(event_id)), account_id=account_id,
                            notification_type=str((payload or {}).get("type", "PAYMENT")),
                            title="Agent-Pay payment notification",
                            payload=payload or {},
                        )
                    mark_published(conn, UUID(str(event_id)))
            processed += 1
        except Exception:
            with connection() as conn:
                with UnitOfWork(conn):
                    mark_failed(
                        conn, UUID(str(event_id)),
                        retry_after_seconds=min(300, 2 ** min(attempts, 8)),
                    )
    return processed
