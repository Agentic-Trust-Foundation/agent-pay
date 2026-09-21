"""Resolve signed provider events into durable payment outcomes."""
import json
from decimal import Decimal
from typing import cast
from uuid import UUID


class ProviderEventResolver:
    """Apply an already-verified provider event exactly once.

    Provider events are persisted/deduplicated before this resolver is called.
    Financial mutation happens only for a newly recorded, valid event.
    """

    def __init__(self, conn):
        self.conn = conn

    def resolve(
        self,
        *,
        event_id: UUID,
        provider_operation_id: UUID,
        outcome: str,
        provider_reference: str | None,
        customer_ledger_account_id: UUID,
        clearing_ledger_account_id: UUID,
        correlation_id: str | None = None,
    ) -> str:
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
            """SELECT po.payment_id, po.operation_type, po.idempotency_key, po.request_payload, po.status,
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
        payment_id, operation_type, _, request_payload, operation_status, request_id, amount, currency, payment_status, reservation_id = row

        if operation_status not in ("UNKNOWN", "PENDING", "PROCESSING"):
            self.conn.execute(
                "UPDATE provider_events SET processing_status='PROCESSED', processed_at=now() WHERE id=%s",
                (event_id,),
            )
            return "IGNORED"

        from .provider import PaymentProvider, ProviderOutcome
        if outcome not in {"SUCCEEDED", "FAILED"}:
            raise ValueError("unsupported provider outcome")
        provider_outcome = ProviderOutcome(outcome)

        payload = request_payload if isinstance(request_payload, dict) else {}
        amount_d = Decimal(str(payload.get("amount", amount)))
        currency_u = str(payload.get("currency", currency)).strip().upper()
        customer_id = payload.get("customer_ledger_account_id") or str(customer_ledger_account_id)
        clearing_id = payload.get("clearing_ledger_account_id") or str(clearing_ledger_account_id)

        if operation_type == "CHARGE":
            if not reservation_id or not customer_id or not clearing_id:
                raise ValueError("charge operation is missing required execution context")
            from .orchestrator import PaymentOrchestrator
            result = PaymentOrchestrator(self.conn, cast(PaymentProvider, None)).finalize(
                payment_id=payment_id,
                payment_request_id=request_id,
                reservation_id=reservation_id,
                amount=amount_d,
                currency=currency_u,
                customer_ledger_account_id=UUID(str(customer_id)),
                clearing_ledger_account_id=UUID(str(clearing_id)),
                outcome=provider_outcome,
                provider_reference=provider_reference,
                correlation_id=correlation_id,
            )
        else:
            from .provider_worker import ProviderOperationWorker
            result = ProviderOperationWorker(self.conn, cast(PaymentProvider, None))._finalize_simple_operation(
                operation_id=provider_operation_id,
                payment_id=payment_id,
                operation_type=operation_type,
                amount=amount_d,
                currency=currency_u,
                outcome=provider_outcome,
                provider_reference=provider_reference,
                customer_ledger_account_id=UUID(str(customer_id)) if customer_id else None,
                clearing_ledger_account_id=UUID(str(clearing_id)) if clearing_id else None,
                correlation_id=correlation_id,
            )

        self.conn.execute(
            """UPDATE provider_operations
               SET response_payload=%s::jsonb
             WHERE id=%s""",
            (json.dumps({"source": "webhook", "event_id": str(event_id), "outcome": outcome}), provider_operation_id),
        )
        self.conn.execute(
            "UPDATE provider_events SET processing_status='PROCESSED', processed_at=now() WHERE id=%s",
            (event_id,),
        )
        return result

    def _create_transaction(
        self,
        *,
        payment_id: UUID,
        type_: str,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
        external_reference: str | None = None,
    ) -> UUID:
        existing = self.conn.execute(
            "SELECT id FROM transactions WHERE idempotency_key=%s",
            (idempotency_key,),
        ).fetchone()
        if existing:
            return existing[0]
        return self.conn.execute(
            """INSERT INTO transactions
               (payment_id, type, status, amount, currency, external_reference,
                idempotency_key, posted_at)
               VALUES (%s,%s,'POSTED',%s,%s,%s,%s,now())
               RETURNING id""",
            (payment_id, type_, str(amount), currency, external_reference, idempotency_key),
        ).fetchone()[0]
