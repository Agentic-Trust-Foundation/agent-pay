"""Durable provider settlement ingestion and reconciliation workflow."""
from decimal import Decimal
from uuid import UUID

from .reconciliation import compare_amounts
from .unit_of_work import UnitOfWork


class SettlementRepository:
    """Persist and reconcile one provider settlement report atomically.

    A settlement report is a provider assertion about one provider operation.
    Reconciliation records the conclusion but never mutates payment, budget, or
    ledger truth automatically.
    """

    def __init__(self, conn):
        self.conn = conn

    def ingest(
        self,
        *,
        provider_name: str,
        settlement_reference: str,
        provider_reference: str,
        observed_amount: str,
        observed_currency: str,
        reported_at=None,
        settled_at=None,
    ) -> str:
        provider_name = provider_name.strip()
        settlement_reference = settlement_reference.strip()
        provider_reference = provider_reference.strip()
        observed_amount_d = Decimal(str(observed_amount))
        observed_currency = observed_currency.strip().upper()

        if not provider_name or not settlement_reference or not provider_reference:
            raise ValueError("provider and settlement references are required")
        if observed_amount_d <= 0:
            raise ValueError("observed settlement amount must be positive")
        if len(observed_currency) != 3:
            raise ValueError("observed settlement currency must be ISO-4217 alpha-3")

        with UnitOfWork(self.conn):
            # The database unique constraint is the concurrency/idempotency
            # boundary. ON CONFLICT avoids a race between SELECT and INSERT.
            inserted = self.conn.execute(
                """INSERT INTO settlements
                   (provider_name, settlement_reference, currency, amount,
                    status, reported_at, settled_at)
                   VALUES (%s,%s,%s,%s,'REPORTED',%s,%s)
                   ON CONFLICT (provider_name, settlement_reference) DO NOTHING
                   RETURNING id""",
                (
                    provider_name,
                    settlement_reference,
                    observed_currency,
                    observed_amount_d,
                    reported_at,
                    settled_at,
                ),
            ).fetchone()

            if not inserted:
                return "DUPLICATE"

            settlement_id = inserted[0]

            operations = self.conn.execute(
                """SELECT po.id, po.status, po.provider_reference, po.operation_type,
                          po.request_payload, p.amount, p.currency
                   FROM provider_operations po
                   JOIN payments p ON p.id=po.payment_id
                   WHERE po.provider_reference=%s
                   ORDER BY po.created_at DESC
                   FOR UPDATE""",
                (provider_reference,),
            ).fetchall()

            if not operations:
                self._record_reconciliation(
                    settlement_id=settlement_id,
                    provider_operation_id=None,
                    status="DISCREPANCY",
                    expected_amount=None,
                    observed_amount=observed_amount_d,
                    expected_currency=None,
                    observed_currency=observed_currency,
                    discrepancy_code="UNKNOWN_PROVIDER_REFERENCE",
                )
                self.conn.execute(
                    "UPDATE settlements SET status='DISCREPANCY' WHERE id=%s",
                    (settlement_id,),
                )
                return "DISCREPANCY"

            if len(operations) > 1:
                self._record_reconciliation(
                    settlement_id=settlement_id,
                    provider_operation_id=None,
                    status="DISCREPANCY",
                    expected_amount=None,
                    observed_amount=observed_amount_d,
                    expected_currency=None,
                    observed_currency=observed_currency,
                    discrepancy_code="AMBIGUOUS_PROVIDER_REFERENCE",
                )
                self.conn.execute(
                    "UPDATE settlements SET status='DISCREPANCY' WHERE id=%s",
                    (settlement_id,),
                )
                return "DISCREPANCY"

            operation_id, operation_status, _, _operation_type, request_payload, payment_amount, payment_currency = operations[0]
            payload = request_payload if isinstance(request_payload, dict) else {}
            expected_amount = payload.get("amount", payment_amount)
            expected_currency = payload.get("currency", payment_currency)
            if operation_status != "SUCCEEDED":
                status, code = "DISCREPANCY", "STATUS_MISMATCH"
            else:
                status, code = compare_amounts(
                    expected_amount=expected_amount,
                    observed_amount=observed_amount_d,
                    expected_currency=expected_currency,
                    observed_currency=observed_currency,
                )
            self._record_reconciliation(
                settlement_id=settlement_id,
                provider_operation_id=operation_id,
                status=status,
                expected_amount=expected_amount,
                observed_amount=observed_amount_d,
                expected_currency=expected_currency,
                observed_currency=observed_currency,
                discrepancy_code=code,
            )
            self.conn.execute(
                "UPDATE settlements SET status=%s WHERE id=%s",
                ("RECONCILED" if status == "MATCHED" else "DISCREPANCY", settlement_id),
            )
            return status

    def _record_reconciliation(
        self,
        *,
        settlement_id: UUID,
        provider_operation_id: UUID | None,
        status: str,
        expected_amount,
        observed_amount,
        expected_currency: str | None,
        observed_currency: str,
        discrepancy_code: str | None,
    ) -> UUID:
        return self.conn.execute(
            """INSERT INTO reconciliation_records
               (settlement_id, provider_operation_id, status,
                expected_amount, observed_amount, expected_currency,
                observed_currency, discrepancy_code)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
               RETURNING id""",
            (
                settlement_id,
                provider_operation_id,
                status,
                expected_amount,
                observed_amount,
                expected_currency,
                observed_currency,
                discrepancy_code,
            ),
        ).fetchone()[0]
