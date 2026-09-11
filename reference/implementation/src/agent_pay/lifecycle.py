"""Capture, void and refund lifecycle with provider idempotency and ledger posting."""
from decimal import Decimal
from uuid import UUID

from .ledger import post_journal
from .provider import PaymentProvider, ProviderOutcome
from .repositories import PaymentRepository


class PaymentLifecycle:
    def __init__(self, conn, provider: PaymentProvider):
        self.conn = conn
        self.provider = provider
        self.payments = PaymentRepository(conn)

    def _operation(self, payment_id: UUID, operation_type: str, key: str) -> UUID:
        return self.payments.create_provider_operation(payment_id, operation_type, key)

    def _amount_minor(self, amount: Decimal) -> int:
        return int(amount * Decimal("100"))

    def _create_transaction(self, *, payment_id: UUID, type_: str, amount: Decimal,
                            currency: str, idempotency_key: str,
                            original_transaction_id: UUID | None = None,
                            external_reference: str | None = None,
                            status: str = "POSTED") -> UUID:
        existing = self.conn.execute(
            "SELECT id FROM transactions WHERE idempotency_key=%s", (idempotency_key,)
        ).fetchone()
        if existing:
            return existing[0]
        return self.conn.execute(
            """INSERT INTO transactions
               (payment_id, type, status, amount, currency, original_transaction_id,
                external_reference, idempotency_key, posted_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,CASE WHEN %s='POSTED' THEN now() ELSE NULL END)
               RETURNING id""",
            (payment_id, type_, status, str(amount), currency, original_transaction_id,
             external_reference, idempotency_key, status),
        ).fetchone()[0]

    def capture(self, *, payment_id: UUID, amount: Decimal, currency: str,
                customer_ledger_account_id: UUID, clearing_ledger_account_id: UUID,
                correlation_id: str | None = None) -> str:
        key = f"payment:{payment_id}:capture"
        # Capture and void are mutually exclusive provider operations. Hold the
        # payment row for the complete lifecycle so concurrent callers cannot
        # both observe AUTHORIZED and initiate conflicting external operations.
        row = self.conn.execute(
            "SELECT id, payment_request_id, amount, currency, status FROM payments WHERE id=%s FOR UPDATE",
            (payment_id,),
        ).fetchone()
        if not row:
            raise ValueError("payment not found")
        if row[4] == "SUCCEEDED":
            return "SUCCEEDED"
        if row[4] != "AUTHORIZED":
            raise ValueError("payment is not authorized for capture")
        self._operation(payment_id, "CAPTURE", key)
        outcome = self.provider.capture(str(payment_id), self._amount_minor(amount), currency, key)
        if outcome == ProviderOutcome.UNKNOWN:
            self.payments.update_status(payment_id, "UNKNOWN_EXTERNAL_OUTCOME")
            return "UNKNOWN_EXTERNAL_OUTCOME"
        if outcome == ProviderOutcome.FAILED:
            self.payments.update_status(payment_id, "FAILED")
            self._create_transaction(payment_id=payment_id, type_="CAPTURE", amount=amount,
                                     currency=currency, idempotency_key=f"tx:{payment_id}:capture:failed",
                                     status="FAILED")
            return "FAILED"
        transaction_id = self._create_transaction(
            payment_id=payment_id, type_="CAPTURE", amount=amount, currency=currency,
            idempotency_key=f"tx:{payment_id}:capture", status="POSTED"
        )
        post_journal(
            self.conn, currency=currency, reference_type="TRANSACTION", reference_id=transaction_id,
            idempotency_key=key, correlation_id=correlation_id,
            postings=[
                {"ledger_account_id": customer_ledger_account_id, "side": "DEBIT", "amount": str(amount), "currency": currency},
                {"ledger_account_id": clearing_ledger_account_id, "side": "CREDIT", "amount": str(amount), "currency": currency},
            ],
        )
        self.payments.update_status(payment_id, "SUCCEEDED")
        return "SUCCEEDED"

    def void(self, *, payment_id: UUID, amount: Decimal, currency: str,
             correlation_id: str | None = None) -> str:
        key = f"payment:{payment_id}:void"
        # Capture and void are mutually exclusive provider operations. The same
        # row lock used by capture prevents a concurrent void from racing it.
        row = self.conn.execute(
            "SELECT id, payment_request_id, amount, currency, status FROM payments WHERE id=%s FOR UPDATE",
            (payment_id,),
        ).fetchone()
        if not row:
            raise ValueError("payment not found")
        if row[4] == "VOIDED":
            return "VOIDED"
        if row[4] != "AUTHORIZED":
            raise ValueError("only an authorized payment can be voided")
        self.payments.update_status(payment_id, "VOID_REQUESTED")
        self._operation(payment_id, "VOID", key)
        outcome = self.provider.void(str(payment_id), self._amount_minor(amount), currency, key)
        if outcome == ProviderOutcome.UNKNOWN:
            self.payments.update_status(payment_id, "UNKNOWN_EXTERNAL_OUTCOME")
            return "UNKNOWN_EXTERNAL_OUTCOME"
        if outcome == ProviderOutcome.FAILED:
            self.payments.update_status(payment_id, "VOID_FAILED")
            self._create_transaction(payment_id=payment_id, type_="VOID", amount=amount, currency=currency,
                                     idempotency_key=f"tx:{payment_id}:void:failed", status="FAILED")
            return "VOID_FAILED"
        self._create_transaction(payment_id=payment_id, type_="VOID", amount=amount, currency=currency,
                                 idempotency_key=f"tx:{payment_id}:void")
        self.payments.update_status(payment_id, "VOIDED")
        return "VOIDED"

    def refund(self, *, payment_id: UUID, amount: Decimal, currency: str,
               customer_ledger_account_id: UUID, clearing_ledger_account_id: UUID,
               correlation_id: str | None = None) -> str:
        key = f"payment:{payment_id}:refund:{amount}:{currency}"
        # Serialize refunds for one payment so two concurrent callers cannot
        # both observe the same remaining refundable amount.
        locked = self.conn.execute(
            "SELECT status FROM payments WHERE id=%s FOR UPDATE", (payment_id,)
        ).fetchone()
        if not locked:
            raise ValueError("payment not found")
        if locked[0] not in ("SUCCEEDED", "REFUND_FAILED"):
            raise ValueError("only a captured payment can be refunded")
        captured = self.conn.execute(
            """SELECT COALESCE(SUM(amount),0) FROM transactions
               WHERE payment_id=%s AND type='CAPTURE' AND status='POSTED'""", (payment_id,)
        ).fetchone()[0]
        refunded = self.conn.execute(
            """SELECT COALESCE(SUM(amount),0) FROM transactions
               WHERE payment_id=%s AND type='REFUND' AND status='POSTED'""", (payment_id,)
        ).fetchone()[0]
        amount_d = Decimal(str(amount))
        if amount_d <= 0 or amount_d > Decimal(str(captured)) - Decimal(str(refunded)):
            raise ValueError("refund amount exceeds refundable captured amount")
        self.payments.update_status(payment_id, "REFUND_PROCESSING")
        self._operation(payment_id, "REFUND", key)
        refund_id = self._create_transaction(payment_id=payment_id, type_="REFUND", amount=amount_d,
                                             currency=currency, idempotency_key=f"tx:{payment_id}:refund:{amount}:{currency}",
                                             status="PENDING")
        outcome = self.provider.refund(str(payment_id), self._amount_minor(amount_d), currency, key)
        if outcome == ProviderOutcome.UNKNOWN:
            self.payments.update_status(payment_id, "UNKNOWN_EXTERNAL_OUTCOME")
            return "UNKNOWN_EXTERNAL_OUTCOME"
        if outcome == ProviderOutcome.FAILED:
            self.conn.execute("UPDATE transactions SET status='FAILED' WHERE id=%s", (refund_id,))
            self.payments.update_status(payment_id, "REFUND_FAILED")
            return "REFUND_FAILED"
        self.conn.execute("UPDATE transactions SET status='POSTED', posted_at=now() WHERE id=%s", (refund_id,))
        post_journal(
            self.conn, currency=currency, reference_type="TRANSACTION", reference_id=refund_id,
            idempotency_key=key, correlation_id=correlation_id,
            postings=[
                {"ledger_account_id": clearing_ledger_account_id, "side": "DEBIT", "amount": str(amount_d), "currency": currency},
                {"ledger_account_id": customer_ledger_account_id, "side": "CREDIT", "amount": str(amount_d), "currency": currency},
            ],
        )
        self.payments.update_status(payment_id, "REFUNDED")
        return "REFUNDED"
