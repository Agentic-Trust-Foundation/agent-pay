"""Durable provider settlement ingestion and reconciliation workflow."""
from decimal import Decimal
from uuid import UUID

from .reconciliation import compare_amounts
from .unit_of_work import UnitOfWork


class SettlementRepository:
    """Persist and reconcile one provider settlement report atomically.

    V1 models a settlement report as a provider assertion about one provider
    operation. The workflow never mutates payment or ledger truth merely because
    a report arrived; reconciliation produces an explicit MATCHED/DISCREPANCY
    conclusion instead.
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
        observed_amount_d = Decimal(str(observed_amount))
        observed_currency = observed_currency.strip().upper()

        with UnitOfWork(self.conn):
            existing = self.conn.execute(
                """SELECT id, status FROM settlements
                   WHERE provider_name=%s AND settlement_reference=%s
                   FOR UPDATE""",
                (provider_name, settlement_reference),
            ).fetchone()
            if existing:
                return "DUPLICATE"

            settlement_id = self.conn.execute(
                """INSERT INTO settlements
                   (provider_name, settlement_reference, currency, amount,
                    status, reported_at, settled_at)
                   VALUES (%s,%s,%s,%s,'REPORTED',%s,%s)
                   RETURNING id""",
                (provider_name, settlement_reference, observed_currency,
                 observed_amount_d, reported_at, settled_at),
            ).fetchone()[0]

            operation = self.conn.execute(
                """SELECT po.id, po.status, po.provider_reference,
                          p.amount, p.currency
                   FROM provider_operations po
                   JOIN payments p ON p.id=po.payment_id
                   WHERE po.provider_reference=%s
                   ORDER BY po.created_at DESC
                   LIMIT 1
                   FOR UPDATE""",
                (provider_reference,),
            ).fetchone()

            if not operation:
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

            operation_id, operation_status, operation_reference, expected_amount, expected_currency = operation
            if operation_reference != provider_reference:
                code = "PROVIDER_REFERENCE_MISMATCH"
                status = "DISCREPANCY"
            elif operation_status != "SUCCEEDED":
                code = "STATUS_MISMATCH"
                status = "DISCREPANCY"
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
        self, *, settlement_id: UUID, provider_operation_id: UUID | None,
        status: str, expected_amount, observed_amount,
        expected_currency: str | None, observed_currency: str,
        discrepancy_code: str | None,
    ) -> UUID:
        return self.conn.execute(
            """INSERT INTO reconciliation_records
               (settlement_id, provider_operation_id, status,
                expected_amount, observed_amount, expected_currency,
                observed_currency, discrepancy_code)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
               RETURNING id""",
            (settlement_id, provider_operation_id, status,
             expected_amount, observed_amount, expected_currency,
             observed_currency, discrepancy_code),
        ).fetchone()[0]
