"""Payment execution worker primitives.

This module intentionally keeps external provider calls outside PostgreSQL transactions.
A production worker can call `process_one` from a durable queue/scheduler.
"""
from decimal import Decimal
from uuid import UUID

from .orchestrator import PaymentOrchestrator
from .provider import PaymentProvider
from .unit_of_work import UnitOfWork


def process_one(*, conn, payment_id: UUID, provider: PaymentProvider,
                customer_ledger_account_id: UUID, clearing_ledger_account_id: UUID,
                correlation_id: str | None = None) -> str:
    """Execute one reserved payment and durably finalize its outcome."""
    with UnitOfWork(conn):
        row = conn.execute(
            """SELECT p.payment_request_id, p.amount, p.currency, pr.budget_reservation_id
               FROM payments p
               JOIN payment_requests pr ON pr.id = p.payment_request_id
               WHERE p.id=%s
               FOR UPDATE""",
            (payment_id,),
        ).fetchone()
        if not row:
            raise ValueError("payment not found")
        request_id, amount, currency, reservation_id = row
        if not reservation_id:
            raise ValueError("payment has no budget reservation")
        amount = Decimal(str(amount))
        orchestrator = PaymentOrchestrator(conn, provider)
        orchestrator.payments.create_provider_operation(
            payment_id, "CHARGE", f"payment:{payment_id}:charge"
        )
        orchestrator.payments.update_status(payment_id, "PROCESSING")

    # The provider call happens after the reservation transaction commits.
    outcome = provider.charge(str(payment_id), int(amount * Decimal("100")), currency)

    with UnitOfWork(conn):
        orchestrator = PaymentOrchestrator(conn, provider)
        return orchestrator.finalize(
            payment_id=payment_id,
            payment_request_id=request_id,
            reservation_id=reservation_id,
            amount=amount,
            currency=currency,
            customer_ledger_account_id=customer_ledger_account_id,
            clearing_ledger_account_id=clearing_ledger_account_id,
            outcome=outcome,
            correlation_id=correlation_id,
        )
