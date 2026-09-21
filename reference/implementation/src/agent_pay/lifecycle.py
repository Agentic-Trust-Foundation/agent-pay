"""Durable capture, void and refund lifecycle preparation.

Provider execution is performed by ProviderOperationWorker outside database
transactions. These methods only validate and persist the provider operation.
"""
from decimal import Decimal
from uuid import UUID

from .provider import PaymentProvider
from .repositories import PaymentRepository


class PaymentLifecycle:
    def __init__(self, conn, provider: PaymentProvider):
        self.conn = conn
        self.provider = provider
        self.payments = PaymentRepository(conn)

    def _operation(self, payment_id: UUID, operation_type: str, key: str,
                   *, amount: Decimal, currency: str,
                   customer_ledger_account_id: UUID | None = None,
                   clearing_ledger_account_id: UUID | None = None) -> UUID:
        payload = {
            "amount": str(amount),
            "currency": currency,
        }
        if customer_ledger_account_id is not None:
            payload["customer_ledger_account_id"] = str(customer_ledger_account_id)
        if clearing_ledger_account_id is not None:
            payload["clearing_ledger_account_id"] = str(clearing_ledger_account_id)
        return self.payments.create_provider_operation(
            payment_id, operation_type, key, request_payload=payload
        )

    @staticmethod
    def _validate_operation_amount(*, requested_amount: Decimal, requested_currency: str,
                                   payment_amount: Decimal, payment_currency: str) -> tuple[Decimal, str]:
        amount = Decimal(str(requested_amount))
        currency = requested_currency.strip().upper()
        if amount <= 0:
            raise ValueError("operation amount must be positive")
        cents = amount * Decimal("100")
        if cents != cents.to_integral_value():
            raise ValueError("reference payment rails support at most two decimal places")
        if amount != Decimal(str(payment_amount)):
            raise ValueError("operation amount does not match payment amount")
        if currency != payment_currency.strip().upper():
            raise ValueError("operation currency does not match payment currency")
        return amount, currency

    @staticmethod
    def _validate_refund_amount(*, requested_amount: Decimal, requested_currency: str,
                                 payment_currency: str) -> tuple[Decimal, str]:
        amount = Decimal(str(requested_amount))
        currency = requested_currency.strip().upper()
        if amount <= 0:
            raise ValueError("operation amount must be positive")
        cents = amount * Decimal("100")
        if cents != cents.to_integral_value():
            raise ValueError("reference payment rails support at most two decimal places")
        if currency != payment_currency.strip().upper():
            raise ValueError("operation currency does not match payment currency")
        return amount, currency

    def _existing_operation(self, payment_id: UUID, operation_type: str, key: str):
        return self.conn.execute(
            """SELECT id, status FROM provider_operations
               WHERE payment_id=%s AND operation_type=%s AND idempotency_key=%s""",
            (payment_id, operation_type, key),
        ).fetchone()

    def capture(self, *, payment_id: UUID, amount: Decimal, currency: str,
                customer_ledger_account_id: UUID, clearing_ledger_account_id: UUID,
                correlation_id: str | None = None) -> str:
        del correlation_id
        row = self.conn.execute(
            "SELECT amount, currency, status FROM payments WHERE id=%s FOR UPDATE",
            (payment_id,),
        ).fetchone()
        if not row:
            raise ValueError("payment not found")
        if row[2] == "SUCCEEDED":
            return "SUCCEEDED"
        if row[2] != "AUTHORIZED":
            raise ValueError("payment is not authorized for capture")
        amount, currency = self._validate_operation_amount(
            requested_amount=amount, requested_currency=currency,
            payment_amount=row[0], payment_currency=row[1],
        )
        key = f"payment:{payment_id}:capture"
        existing = self._existing_operation(payment_id, "CAPTURE", key)
        if existing and existing[1] in {"PENDING", "PROCESSING", "UNKNOWN"}:
            return "UNKNOWN_EXTERNAL_OUTCOME" if existing[1] == "UNKNOWN" else "PROCESSING"
        self._operation(
            payment_id, "CAPTURE", key, amount=amount, currency=currency,
            customer_ledger_account_id=customer_ledger_account_id,
            clearing_ledger_account_id=clearing_ledger_account_id,
        )
        return "PROCESSING"

    def void(self, *, payment_id: UUID, amount: Decimal, currency: str,
             correlation_id: str | None = None) -> str:
        del correlation_id
        row = self.conn.execute(
            "SELECT amount, currency, status FROM payments WHERE id=%s FOR UPDATE",
            (payment_id,),
        ).fetchone()
        if not row:
            raise ValueError("payment not found")
        if row[2] == "VOIDED":
            return "VOIDED"
        if row[2] not in {"AUTHORIZED", "VOID_REQUESTED"}:
            raise ValueError("only an authorized payment can be voided")
        amount, currency = self._validate_operation_amount(
            requested_amount=amount, requested_currency=currency,
            payment_amount=row[0], payment_currency=row[1],
        )
        key = f"payment:{payment_id}:void"
        existing = self._existing_operation(payment_id, "VOID", key)
        if existing and existing[1] in {"PENDING", "PROCESSING", "UNKNOWN"}:
            return "UNKNOWN_EXTERNAL_OUTCOME" if existing[1] == "UNKNOWN" else "VOID_REQUESTED"
        self.payments.update_status(payment_id, "VOID_REQUESTED")
        self._operation(payment_id, "VOID", key, amount=amount, currency=currency)
        return "VOID_REQUESTED"

    def refund(self, *, payment_id: UUID, amount: Decimal, currency: str,
               customer_ledger_account_id: UUID, clearing_ledger_account_id: UUID,
               correlation_id: str | None = None) -> str:
        del correlation_id
        locked = self.conn.execute(
            "SELECT status, amount, currency FROM payments WHERE id=%s FOR UPDATE",
            (payment_id,),
        ).fetchone()
        if not locked:
            raise ValueError("payment not found")
        if locked[0] not in ("SUCCEEDED", "REFUND_FAILED", "REFUNDED"):
            raise ValueError("only a captured payment can be refunded")
        amount, currency = self._validate_refund_amount(
            requested_amount=amount, requested_currency=currency,
            payment_currency=locked[2],
        )
        key = f"payment:{payment_id}:refund:{amount}:{currency}"
        existing = self._existing_operation(payment_id, "REFUND", key)
        if existing:
            if existing[1] == "SUCCEEDED":
                return "REFUNDED" if locked[0] == "REFUNDED" else "SUCCEEDED"
            if existing[1] in {"PENDING", "PROCESSING", "UNKNOWN"}:
                return "UNKNOWN_EXTERNAL_OUTCOME" if existing[1] == "UNKNOWN" else "REFUND_PROCESSING"

        captured = self.conn.execute(
            """SELECT COALESCE(SUM(amount),0) FROM transactions
               WHERE payment_id=%s AND type='CAPTURE' AND status='POSTED'""",
            (payment_id,),
        ).fetchone()[0]
        refunded = self.conn.execute(
            """SELECT COALESCE(SUM(amount),0) FROM transactions
               WHERE payment_id=%s AND type='REFUND' AND status='POSTED'""",
            (payment_id,),
        ).fetchone()[0]
        if amount > Decimal(str(captured)) - Decimal(str(refunded)):
            raise ValueError("refund amount exceeds refundable captured amount")

        self.payments.update_status(payment_id, "REFUND_PROCESSING")
        self._operation(
            payment_id, "REFUND", key, amount=amount, currency=currency,
            customer_ledger_account_id=customer_ledger_account_id,
            clearing_ledger_account_id=clearing_ledger_account_id,
        )
        tx_key = f"tx:{payment_id}:refund:{amount}:{currency}"
        existing_tx = self.conn.execute(
            "SELECT id, status FROM transactions WHERE idempotency_key=%s",
            (tx_key,),
        ).fetchone()
        if not existing_tx:
            self.conn.execute(
                """INSERT INTO transactions
                   (payment_id, type, status, amount, currency, idempotency_key)
                   VALUES (%s,'REFUND','PENDING',%s,%s,%s)""",
                (payment_id, str(amount), currency, tx_key),
            )
        return "REFUND_PROCESSING"
