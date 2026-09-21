"""Execute durable provider operations outside database transactions."""
import json
from decimal import Decimal
from uuid import UUID

from .orchestrator import PaymentOrchestrator
from .provider import PaymentProvider, ProviderOutcome


class ProviderOperationWorker:
    """Claim durable provider work, execute externally, then finalize in a new tx."""

    def __init__(self, conn, provider: PaymentProvider):
        self.conn = conn
        self.provider = provider

    def claim(self):
        with self.conn.transaction():
            row = self.conn.execute(
                """SELECT po.id, po.payment_id, po.operation_type, po.idempotency_key,
                          po.request_payload, p.payment_request_id, p.amount, p.currency
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

    def retry_unknown(self, operation_id: UUID) -> bool:
        with self.conn.transaction():
            result = self.conn.execute(
                """UPDATE provider_operations
                   SET status='PENDING', completed_at=NULL
                 WHERE id=%s AND status='UNKNOWN'""",
                (operation_id,),
            )
            return result.rowcount == 1

    def run_once(self, *, customer_ledger_account_id: UUID | None = None,
                 clearing_ledger_account_id: UUID | None = None,
                 correlation_id: str | None = None) -> str | None:
        operation = self.claim()
        if operation is None:
            return None

        operation_id, payment_id, operation_type, idempotency_key, payload, request_id, payment_amount, payment_currency = operation
        details = json.loads(payload or "{}")
        amount = Decimal(str(details.get("amount", payment_amount)))
        currency = str(details.get("currency", payment_currency)).strip().upper()
        customer = UUID(str(details["customer_ledger_account_id"])) if details.get("customer_ledger_account_id") else customer_ledger_account_id
        clearing = UUID(str(details["clearing_ledger_account_id"])) if details.get("clearing_ledger_account_id") else clearing_ledger_account_id
        try:
            outcome = self._call_provider(
                operation_type=operation_type,
                payment_id=payment_id,
                amount_minor=self._amount_minor(amount),
                currency=currency,
                idempotency_key=idempotency_key,
            )
        except Exception as exc:
            with self.conn.transaction():
                self.conn.execute(
                    """UPDATE provider_operations
                       SET status='PENDING', response_payload=%s::jsonb
                       WHERE id=%s AND status='PROCESSING'""",
                    (json.dumps({"error": str(exc)}), operation_id),
                )
            return "RETRY_PENDING"

        provider_reference = getattr(self.provider, "reference_for", lambda _key: None)(idempotency_key)
        with self.conn.transaction():
            if operation_type == "CHARGE":
                if customer is None or clearing is None:
                    raise ValueError("ledger accounts are required for charge finalization")
                return PaymentOrchestrator(self.conn, self.provider).finalize(
                    payment_id=payment_id,
                    payment_request_id=request_id,
                    reservation_id=self._reservation_id(request_id),
                    amount=amount,
                    currency=currency,
                    customer_ledger_account_id=customer,
                    clearing_ledger_account_id=clearing,
                    outcome=outcome,
                    provider_reference=provider_reference,
                    correlation_id=correlation_id,
                )
            return self._finalize_simple_operation(
                operation_id=operation_id, payment_id=payment_id,
                operation_type=operation_type, amount=amount, currency=currency,
                outcome=outcome, provider_reference=provider_reference,
                customer_ledger_account_id=customer,
                clearing_ledger_account_id=clearing,
                correlation_id=correlation_id,
            )

    @staticmethod
    def _amount_minor(amount: Decimal) -> int:
        cents = amount * Decimal("100")
        if amount <= 0 or cents != cents.to_integral_value():
            raise ValueError("provider operation amount must be positive and have at most two decimals")
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
                                    customer_ledger_account_id: UUID | None,
                                    clearing_ledger_account_id: UUID | None,
                                    correlation_id: str | None) -> str:
        if outcome == ProviderOutcome.UNKNOWN:
            status = "UNKNOWN"
            payment_status = "UNKNOWN_EXTERNAL_OUTCOME"
        elif outcome == ProviderOutcome.FAILED:
            status = "FAILED"
            payment_status = {
                "CAPTURE": "FAILED", "VOID": "VOID_FAILED", "REFUND": "REFUND_FAILED",
            }[operation_type]
        else:
            status = "SUCCEEDED"
            payment_status = {"CAPTURE": "SUCCEEDED", "VOID": "VOIDED", "REFUND": "REFUNDED"}[operation_type]

        if operation_type in {"CAPTURE", "REFUND"} and outcome == ProviderOutcome.SUCCEEDED:
            if customer_ledger_account_id is None or clearing_ledger_account_id is None:
                raise ValueError("ledger accounts are required for capture/refund finalization")

        self.conn.execute(
            """UPDATE provider_operations
               SET status=%s, provider_reference=COALESCE(%s, provider_reference),
                   completed_at=CASE WHEN %s IN ('SUCCEEDED','FAILED','UNKNOWN') THEN now() ELSE completed_at END
             WHERE id=%s AND status='PROCESSING'""",
            (status, provider_reference, status, operation_id),
        )

        if outcome == ProviderOutcome.SUCCEEDED:
            if operation_type == "REFUND":
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
                tx_key = f"tx:{payment_id}:refund:{amount}:{currency}"
                tx = self.conn.execute(
                    "SELECT id FROM transactions WHERE idempotency_key=%s FOR UPDATE",
                    (tx_key,),
                ).fetchone()
                if not tx:
                    tx = self.conn.execute(
                        """INSERT INTO transactions
                           (payment_id,type,status,amount,currency,external_reference,idempotency_key,posted_at)
                           VALUES (%s,'REFUND','POSTED',%s,%s,%s,%s,now()) RETURNING id""",
                        (payment_id, str(amount), currency, provider_reference, tx_key),
                    ).fetchone()
                else:
                    self.conn.execute(
                        "UPDATE transactions SET status='POSTED', external_reference=COALESCE(%s,external_reference), posted_at=now() WHERE id=%s",
                        (provider_reference, tx[0]),
                    )
                from .ledger import post_journal
                post_journal(
                    self.conn, currency=currency, reference_type="TRANSACTION",
                    reference_id=tx[0], idempotency_key=f"payment:{payment_id}:refund:{amount}:{currency}",
                    correlation_id=correlation_id,
                    postings=[
                        {"ledger_account_id": clearing_ledger_account_id, "side": "DEBIT", "amount": str(amount), "currency": currency},
                        {"ledger_account_id": customer_ledger_account_id, "side": "CREDIT", "amount": str(amount), "currency": currency},
                    ],
                )
            elif operation_type == "CAPTURE":
                tx_key = f"tx:{payment_id}:capture"
                tx = self.conn.execute(
                    "SELECT id FROM transactions WHERE idempotency_key=%s FOR UPDATE",
                    (tx_key,),
                ).fetchone()
                if not tx:
                    tx = self.conn.execute(
                        """INSERT INTO transactions
                           (payment_id,type,status,amount,currency,external_reference,idempotency_key,posted_at)
                           VALUES (%s,'CAPTURE','POSTED',%s,%s,%s,%s,now()) RETURNING id""",
                        (payment_id, str(amount), currency, provider_reference, tx_key),
                    ).fetchone()
                from .ledger import post_journal
                post_journal(
                    self.conn, currency=currency, reference_type="TRANSACTION",
                    reference_id=tx[0], idempotency_key=f"payment:{payment_id}:capture",
                    correlation_id=correlation_id,
                    postings=[
                        {"ledger_account_id": customer_ledger_account_id, "side": "DEBIT", "amount": str(amount), "currency": currency},
                        {"ledger_account_id": clearing_ledger_account_id, "side": "CREDIT", "amount": str(amount), "currency": currency},
                    ],
                )
            elif operation_type == "VOID":
                tx_key = f"tx:{payment_id}:void"
                self.conn.execute(
                    """INSERT INTO transactions
                       (payment_id,type,status,amount,currency,external_reference,idempotency_key,posted_at)
                       VALUES (%s,'VOID','POSTED',%s,%s,%s,%s,now())
                       ON CONFLICT (idempotency_key) DO UPDATE SET external_reference=EXCLUDED.external_reference""",
                    (payment_id, str(amount), currency, provider_reference, tx_key),
                )

        if outcome == ProviderOutcome.FAILED and operation_type == "REFUND":
            self.conn.execute(
                "UPDATE transactions SET status='FAILED' WHERE idempotency_key=%s",
                (f"tx:{payment_id}:refund:{amount}:{currency}",),
            )

        if operation_type == "REFUND" and outcome == ProviderOutcome.SUCCEEDED:
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
            payment_status = "REFUNDED" if Decimal(str(captured)) == Decimal(str(refunded)) else "SUCCEEDED"

        self.conn.execute(
            """UPDATE payments
               SET status=%s, provider_reference=COALESCE(%s, provider_reference),
                   completed_at=CASE WHEN %s IN ('SUCCEEDED','FAILED','VOIDED','REFUNDED') THEN now() ELSE completed_at END,
                   updated_at=now()
             WHERE id=%s""",
            (payment_status, provider_reference, payment_status, payment_id),
        )
        return payment_status
