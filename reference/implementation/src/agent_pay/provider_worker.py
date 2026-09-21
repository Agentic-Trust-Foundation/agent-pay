"""Execute durable provider operations outside database transactions."""
from decimal import Decimal
from uuid import UUID

from .orchestrator import PaymentOrchestrator
from .provider import PaymentProvider, ProviderOutcome


class ProviderOperationWorker:
    """Claim one durable provider operation, call the provider, then finalize.

    The provider call is deliberately outside any database transaction. A
    transaction only claims the operation or records its outcome.
    """

    def __init__(self, conn, provider: PaymentProvider):
        self.conn = conn
        self.provider = provider

    def claim(self):
        with self.conn.transaction():
            row = self.conn.execute(
                """SELECT po.id, po.payment_id, po.operation_type, po.idempotency_key,
                          p.payment_request_id, p.amount, p.currency
                     FROM provider_operations po
                     JOIN payments p ON p.id=po.payment_id
                    WHERE po.status='PENDING'
                    ORDER BY po.created_at
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1"""
            ).fetchone()
            if not row:
                return None
            self.conn.execute(
                """UPDATE provider_operations
                   SET status='PROCESSING'
                   WHERE id=%s AND status='PENDING'""",
                (row[0],),
            )
            return row

    def run_once(self, *, customer_ledger_account_id: UUID, clearing_ledger_account_id: UUID,
                 correlation_id: str | None = None) -> str | None:
        operation = self.claim()
        if operation is None:
            return None

        operation_id, payment_id, operation_type, idempotency_key, request_id, amount, currency = operation
        amount_d = Decimal(str(amount))
        currency_u = currency.strip().upper()

        # No DB transaction is open here.
        outcome = self._call_provider(
            operation_type=operation_type,
            payment_id=payment_id,
            amount_minor=self._amount_minor(amount_d),
            currency=currency_u,
            idempotency_key=idempotency_key,
        )
        provider_reference = getattr(self.provider, "reference_for", lambda _key: None)(idempotency_key)

        with self.conn.transaction():
            if operation_type == "CHARGE":
                return PaymentOrchestrator(self.conn, self.provider).finalize(
                    payment_id=payment_id,
                    payment_request_id=request_id,
                    reservation_id=self._reservation_id(request_id),
                    amount=amount_d,
                    currency=currency_u,
                    customer_ledger_account_id=customer_ledger_account_id,
                    clearing_ledger_account_id=clearing_ledger_account_id,
                    outcome=outcome,
                    provider_reference=provider_reference,
                    correlation_id=correlation_id,
                )
            self._finalize_simple_operation(
                operation_id=operation_id,
                payment_id=payment_id,
                operation_type=operation_type,
                amount=amount_d,
                currency=currency_u,
                outcome=outcome,
                provider_reference=provider_reference,
                customer_ledger_account_id=customer_ledger_account_id,
                clearing_ledger_account_id=clearing_ledger_account_id,
                correlation_id=correlation_id,
            )
            return outcome.value

    @staticmethod
    def _amount_minor(amount: Decimal) -> int:
        cents = amount * Decimal("100")
        if cents != cents.to_integral_value():
            raise ValueError("reference payment rails support at most two decimal places")
        if amount <= 0:
            raise ValueError("operation amount must be positive")
        return int(cents)

    def _reservation_id(self, request_id: UUID) -> UUID:
        row = self.conn.execute(
            "SELECT budget_reservation_id FROM payment_requests WHERE id=%s",
            (request_id,),
        ).fetchone()
        if not row or not row[0]:
            raise ValueError("payment request has no budget reservation")
        return row[0]

    def _call_provider(self, *, operation_type: str, payment_id: UUID, amount_minor: int,
                       currency: str, idempotency_key: str) -> ProviderOutcome:
        payment_id_s = str(payment_id)
        if operation_type == "CHARGE":
            return self.provider.charge(payment_id_s, amount_minor, currency, idempotency_key)
        if operation_type == "CAPTURE":
            return self.provider.capture(payment_id_s, amount_minor, currency, idempotency_key)
        if operation_type == "VOID":
            return self.provider.void(payment_id_s, amount_minor, currency, idempotency_key)
        if operation_type == "REFUND":
            return self.provider.refund(payment_id_s, amount_minor, currency, idempotency_key)
        raise ValueError(f"unsupported provider operation: {operation_type}")

    def _finalize_simple_operation(self, *, operation_id: UUID, payment_id: UUID,
                                    operation_type: str, amount: Decimal, currency: str,
                                    outcome: ProviderOutcome, provider_reference: str | None,
                                    customer_ledger_account_id: UUID,
                                    clearing_ledger_account_id: UUID,
                                    correlation_id: str | None) -> None:
        if outcome == ProviderOutcome.UNKNOWN:
            status = "UNKNOWN"
            payment_status = "UNKNOWN_EXTERNAL_OUTCOME"
        elif outcome == ProviderOutcome.FAILED:
            status = "FAILED"
            payment_status = {
                "CAPTURE": "FAILED",
                "VOID": "VOID_FAILED",
                "REFUND": "REFUND_FAILED",
            }[operation_type]
        else:
            status = "SUCCEEDED"
            payment_status = {
                "CAPTURE": "SUCCEEDED",
                "VOID": "VOIDED",
                "REFUND": "REFUNDED",
            }[operation_type]

        self.conn.execute(
            """UPDATE provider_operations
               SET status=%s, provider_reference=COALESCE(%s, provider_reference),
                   completed_at=CASE WHEN %s IN ('SUCCEEDED','FAILED','UNKNOWN') THEN now() ELSE completed_at END
             WHERE id=%s""",
            (status, provider_reference, status, operation_id),
        )

        if outcome == ProviderOutcome.SUCCEEDED:
            if operation_type == "REFUND":
                transaction_id = self.conn.execute(
                    """INSERT INTO transactions
                       (payment_id, type, status, amount, currency, external_reference,
                        idempotency_key, posted_at)
                       VALUES (%s,'REFUND','POSTED',%s,%s,%s,%s,now())
                       ON CONFLICT (idempotency_key) DO UPDATE SET idempotency_key=EXCLUDED.idempotency_key
                       RETURNING id""",
                    (payment_id, str(amount), currency, provider_reference, f"tx:{payment_id}:refund:{amount}:{currency}"),
                ).fetchone()[0]
                from .ledger import post_journal
                post_journal(
                    self.conn,
                    currency=currency,
                    reference_type="TRANSACTION",
                    reference_id=transaction_id,
                    idempotency_key=f"payment:{payment_id}:refund:{amount}:{currency}",
                    correlation_id=correlation_id,
                    postings=[
                        {"ledger_account_id": clearing_ledger_account_id, "side": "DEBIT", "amount": str(amount), "currency": currency},
                        {"ledger_account_id": customer_ledger_account_id, "side": "CREDIT", "amount": str(amount), "currency": currency},
                    ],
                )
            elif operation_type == "CAPTURE":
                transaction_id = self.conn.execute(
                    """INSERT INTO transactions
                       (payment_id, type, status, amount, currency, external_reference,
                        idempotency_key, posted_at)
                       VALUES (%s,'CAPTURE','POSTED',%s,%s,%s,%s,now())
                       ON CONFLICT (idempotency_key) DO UPDATE SET idempotency_key=EXCLUDED.idempotency_key
                       RETURNING id""",
                    (payment_id, str(amount), currency, provider_reference, f"tx:{payment_id}:capture"),
                ).fetchone()[0]
                from .ledger import post_journal
                post_journal(
                    self.conn,
                    currency=currency,
                    reference_type="TRANSACTION",
                    reference_id=transaction_id,
                    idempotency_key=f"payment:{payment_id}:capture",
                    correlation_id=correlation_id,
                    postings=[
                        {"ledger_account_id": customer_ledger_account_id, "side": "DEBIT", "amount": str(amount), "currency": currency},
                        {"ledger_account_id": clearing_ledger_account_id, "side": "CREDIT", "amount": str(amount), "currency": currency},
                    ],
                )
        self.conn.execute(
            """UPDATE payments
               SET status=%s, provider_reference=COALESCE(%s, provider_reference),
                   completed_at=CASE WHEN %s IN ('SUCCEEDED','FAILED','VOIDED','REFUNDED') THEN now() ELSE completed_at END,
                   updated_at=now()
             WHERE id=%s""",
            (payment_status, provider_reference, payment_status, payment_id),
        )
