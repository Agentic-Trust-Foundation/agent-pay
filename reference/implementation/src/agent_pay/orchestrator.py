"""Persistence-backed payment orchestration.

External provider execution is intentionally outside database transactions. The
state machine is: persist intent/reservation -> execute provider -> finalize in a
new transaction. Ambiguous provider outcomes remain UNKNOWN_EXTERNAL_OUTCOME.
"""
from decimal import Decimal
from uuid import UUID

from .ledger import post_journal
from .outbox import enqueue
from .provider import PaymentProvider, ProviderOutcome
from .repositories import BudgetRepository, PaymentRepository


class PaymentOrchestrator:
    def __init__(self, conn, provider: PaymentProvider):
        self.conn = conn
        self.provider = provider
        self.payments = PaymentRepository(conn)
        self.budgets = BudgetRepository(conn)

    def prepare(self, *, payment_id: UUID, payment_request_id: UUID, budget_id: UUID,
                amount: Decimal, currency: str, correlation_id: str | None = None) -> UUID:
        reservation_id = self.budgets.reserve(budget_id, payment_request_id, str(amount))
        if reservation_id is None:
            self.payments.update_status(payment_id, "FAILED")
            enqueue(self.conn, event_type="PaymentFailed", aggregate_type="payment",
                    aggregate_id=payment_id, payload={"reason": "BUDGET_INSUFFICIENT"},
                    correlation_id=correlation_id)
            raise ValueError("budget insufficient")
        self.conn.execute(
            "UPDATE payment_requests SET budget_reservation_id=%s WHERE id=%s",
            (reservation_id, payment_request_id),
        )
        self.payments.update_status(payment_id, "PROCESSING")
        enqueue(self.conn, event_type="PaymentStarted", aggregate_type="payment",
                aggregate_id=payment_id, payload={"reservation_id": str(reservation_id)},
                correlation_id=correlation_id)
        return reservation_id

    def execute_external(self, *, payment_id: UUID, amount: Decimal, currency: str) -> ProviderOutcome:
        return self.provider.charge(
            str(payment_id),
            int(amount * Decimal("100")),
            currency,
            f"payment:{payment_id}:charge",
        )

    def finalize(self, *, payment_id: UUID, payment_request_id: UUID, reservation_id: UUID,
                 amount: Decimal, currency: str, customer_ledger_account_id: UUID,
                 clearing_ledger_account_id: UUID, outcome: ProviderOutcome,
                 provider_reference: str | None = None,
                 correlation_id: str | None = None) -> str:
        if outcome == ProviderOutcome.UNKNOWN:
            self.payments.update_status(payment_id, "UNKNOWN_EXTERNAL_OUTCOME", provider_reference)
            enqueue(self.conn, event_type="PaymentOutcomeUnknown", aggregate_type="payment",
                    aggregate_id=payment_id, payload={"reservation_id": str(reservation_id)},
                    correlation_id=correlation_id)
            return "UNKNOWN_EXTERNAL_OUTCOME"

        if outcome == ProviderOutcome.FAILED:
            self.budgets.release(reservation_id)
            self.payments.update_status(payment_id, "FAILED", provider_reference)
            enqueue(self.conn, event_type="PaymentFailed", aggregate_type="payment",
                    aggregate_id=payment_id, payload={"reservation_id": str(reservation_id)},
                    correlation_id=correlation_id)
            return "FAILED"

        self.budgets.consume(reservation_id)
        post_journal(
            self.conn,
            currency=currency,
            reference_type="PAYMENT",
            reference_id=payment_id,
            idempotency_key=f"payment:{payment_id}:capture",
            correlation_id=correlation_id,
            postings=[
                {"ledger_account_id": customer_ledger_account_id, "side": "DEBIT",
                 "amount": str(amount), "currency": currency},
                {"ledger_account_id": clearing_ledger_account_id, "side": "CREDIT",
                 "amount": str(amount), "currency": currency},
            ],
        )
        self.payments.update_status(payment_id, "SUCCEEDED", provider_reference)
        enqueue(self.conn, event_type="PaymentSucceeded", aggregate_type="payment",
                aggregate_id=payment_id, payload={"amount": str(amount), "currency": currency},
                correlation_id=correlation_id)
        return "SUCCEEDED"
