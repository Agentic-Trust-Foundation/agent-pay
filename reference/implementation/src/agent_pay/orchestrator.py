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
        bound = self.conn.execute(
            """SELECT p.payment_request_id, p.status,
                      pr.account_id, pr.agent_id, pr.amount, pr.currency,
                      pr.authorization_evidence_id, ae.verification_status
                 FROM payments p
                 JOIN payment_requests pr ON pr.id=p.payment_request_id
                 LEFT JOIN authorization_evidence ae ON ae.id=pr.authorization_evidence_id
                WHERE p.id=%s AND pr.id=%s
                FOR UPDATE""",
            (payment_id, payment_request_id),
        ).fetchone()
        if not bound:
            raise ValueError("payment and payment request binding is invalid")
        if bound[6] is None or bound[7] != "VERIFIED":
            raise PermissionError("verified authorization evidence is required before execution")
        if Decimal(str(bound[4])) != amount or bound[5].strip().upper() != currency.upper():
            raise ValueError("execution amount/currency does not match payment intent")
        if bound[1] in {"SUCCEEDED", "FAILED", "CANCELLED", "VOIDED", "REFUNDED"}:
            raise ValueError("payment is already terminal")
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
        row = self.conn.execute(
            """SELECT p.payment_request_id, p.status, p.amount, p.currency
                 FROM payments p WHERE p.id=%s FOR UPDATE""",
            (payment_id,),
        ).fetchone()
        if not row or row[0] != payment_request_id:
            raise ValueError("payment and payment request binding is invalid")
        if Decimal(str(row[2])) != amount or row[3].strip().upper() != currency.upper():
            raise ValueError("finalization amount/currency does not match payment")
        if row[1] == "SUCCEEDED" and outcome == ProviderOutcome.SUCCEEDED:
            return "SUCCEEDED"
        if row[1] == "FAILED" and outcome == ProviderOutcome.FAILED:
            return "FAILED"
        if row[1] == "UNKNOWN_EXTERNAL_OUTCOME" and outcome == ProviderOutcome.UNKNOWN:
            return "UNKNOWN_EXTERNAL_OUTCOME"
        if row[1] not in {"PROCESSING", "UNKNOWN_EXTERNAL_OUTCOME"}:
            raise ValueError("payment is not in an executable finalization state")
        if outcome == ProviderOutcome.UNKNOWN:
            self.conn.execute(
                """UPDATE provider_operations
                   SET status='UNKNOWN'
                 WHERE payment_id=%s AND operation_type='CHARGE'""",
                (payment_id,),
            )
            self.payments.update_status(payment_id, "UNKNOWN_EXTERNAL_OUTCOME", provider_reference)
            enqueue(self.conn, event_type="PaymentOutcomeUnknown", aggregate_type="payment",
                    aggregate_id=payment_id, payload={"reservation_id": str(reservation_id)},
                    correlation_id=correlation_id)
            return "UNKNOWN_EXTERNAL_OUTCOME"

        if outcome == ProviderOutcome.FAILED:
            self.conn.execute(
                """UPDATE provider_operations
                   SET status='FAILED', provider_reference=COALESCE(%s, provider_reference),
                       completed_at=now()
                 WHERE payment_id=%s AND operation_type='CHARGE'""",
                (provider_reference, payment_id),
            )
            self.budgets.release(reservation_id)
            self.payments.update_status(payment_id, "FAILED", provider_reference)
            enqueue(self.conn, event_type="PaymentFailed", aggregate_type="payment",
                    aggregate_id=payment_id, payload={"reservation_id": str(reservation_id)},
                    correlation_id=correlation_id)
            return "FAILED"

        self.conn.execute(
            """UPDATE provider_operations
               SET status='SUCCEEDED', provider_reference=COALESCE(%s, provider_reference),
                   completed_at=now()
             WHERE payment_id=%s AND operation_type='CHARGE'""",
            (provider_reference, payment_id),
        )
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
