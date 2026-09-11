"""Resolve signed provider events into durable payment outcomes."""
from decimal import Decimal
from uuid import UUID

from .ledger import post_journal
from .repositories import PaymentRepository
from .unit_of_work import UnitOfWork


class ProviderEventResolver:
    """Apply an already-verified provider event exactly once.

    The provider event is persisted/deduplicated before this resolver is called.
    Financial mutation happens only for a newly recorded, valid event.
    """

    def __init__(self, conn):
        self.conn = conn

    def resolve(self, *, event_id: UUID, provider_operation_id: UUID,
                outcome: str, provider_reference: str | None,
                customer_ledger_account_id: UUID,
                clearing_ledger_account_id: UUID,
                correlation_id: str | None = None) -> str:
        with UnitOfWork(self.conn):
            event = self.conn.execute(
                "SELECT processing_status, signature_valid FROM provider_events WHERE id=%s FOR UPDATE",
                (event_id,),
            ).fetchone()
            if not event:
                raise ValueError("provider event not found")
            if not event[1]:
                raise PermissionError("provider event signature is not valid")
            if event[0] == "PROCESSED":
                return "DUPLICATE"

            row = self.conn.execute(
                """SELECT po.payment_id, po.operation_type, po.idempotency_key,
                          p.payment_request_id, p.amount, p.currency, p.status,
                          pr.budget_reservation_id
                   FROM provider_operations po
                   JOIN payments p ON p.id=po.payment_id
                   JOIN payment_requests pr ON pr.id=p.payment_request_id
                   WHERE po.id=%s FOR UPDATE""",
                (provider_operation_id,),
            ).fetchone()
            if not row:
                raise ValueError("provider operation not found")
            payment_id, operation_type, _, request_id, amount, currency, status, reservation_id = row

            if status not in ("UNKNOWN_EXTERNAL_OUTCOME", "PROCESSING", "PAYMENT_PENDING"):
                self.conn.execute(
                    "UPDATE provider_events SET processing_status='PROCESSED', processed_at=now() WHERE id=%s",
                    (event_id,),
                )
                return "IGNORED"

            if outcome == "SUCCEEDED":
                if operation_type == "CHARGE":
                    if not reservation_id:
                        raise ValueError("successful charge has no budget reservation")
                    self.conn.execute(
                        "UPDATE provider_operations SET status='SUCCEEDED', provider_reference=%s, completed_at=now() WHERE id=%s",
                        (provider_reference, provider_operation_id),
                    )
                    self.conn.execute(
                        "UPDATE payments SET status='SUCCEEDED', provider_reference=COALESCE(%s, provider_reference), completed_at=now(), updated_at=now() WHERE id=%s",
                        (provider_reference, payment_id),
                    )
                    from .repositories import BudgetRepository
                    BudgetRepository(self.conn).consume(reservation_id)
                    customer = Decimal(str(amount))
                    post_journal(
                        self.conn, currency=currency.strip().upper(), reference_type="PAYMENT",
                        reference_id=payment_id, idempotency_key=f"payment:{payment_id}:capture:ledger",
                        correlation_id=correlation_id,
                        postings=[
                            {"ledger_account_id": str(customer_ledger_account_id), "side": "CREDIT", "amount": customer, "currency": currency.strip().upper()},
                            {"ledger_account_id": str(clearing_ledger_account_id), "side": "DEBIT", "amount": customer, "currency": currency.strip().upper()},
                        ],
                    )
                else:
                    self.conn.execute(
                        "UPDATE provider_operations SET status='SUCCEEDED', provider_reference=%s, completed_at=now() WHERE id=%s",
                        (provider_reference, provider_operation_id),
                    )
            elif outcome == "FAILED":
                self.conn.execute(
                    "UPDATE provider_operations SET status='FAILED', provider_reference=%s, completed_at=now() WHERE id=%s",
                    (provider_reference, provider_operation_id),
                )
                if operation_type == "CHARGE" and reservation_id:
                    from .repositories import BudgetRepository
                    BudgetRepository(self.conn).release(reservation_id)
                self.conn.execute(
                    "UPDATE payments SET status='FAILED', provider_reference=COALESCE(%s, provider_reference), completed_at=now(), updated_at=now() WHERE id=%s",
                    (provider_reference, payment_id),
                )
            else:
                raise ValueError("unsupported provider outcome")

            self.conn.execute(
                "UPDATE provider_events SET processing_status='PROCESSED', processed_at=now() WHERE id=%s",
                (event_id,),
            )
            return "RESOLVED"
