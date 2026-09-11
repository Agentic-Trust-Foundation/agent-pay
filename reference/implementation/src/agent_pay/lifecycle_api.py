"""HTTP lifecycle endpoints for capture, void and refund."""
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from .db import connection
from .lifecycle import PaymentLifecycle
from .provider import MockProvider
from .unit_of_work import UnitOfWork

router = APIRouter(tags=["Payment Lifecycle"])


class LifecycleAmount(BaseModel):
    amount: str = Field(pattern=r"^\d+(\.\d{1,4})?$")
    currency: str = Field(min_length=3, max_length=3)


def _accounts(conn, payment_id: UUID):
    row = conn.execute(
        """SELECT la.id,
                  (SELECT ppa.ledger_account_id
                     FROM payment_provider_accounts ppa
                    WHERE ppa.provider_name='mock'
                      AND ppa.currency=p.currency
                      AND ppa.status='ACTIVE')
             FROM payments p
             JOIN payment_requests pr ON pr.id=p.payment_request_id
             JOIN wallets w ON w.account_id=pr.account_id
                  AND w.currency=p.currency AND w.status='ACTIVE'
             JOIN ledger_accounts la ON la.wallet_id=w.id
            WHERE p.id=%s LIMIT 1""",
        (payment_id,),
    ).fetchone()
    if not row or not row[0] or not row[1]:
        raise HTTPException(status_code=409, detail="ledger accounts are not configured")
    return UUID(str(row[0])), UUID(str(row[1]))


def _run(payment_id: UUID, amount: LifecycleAmount, operation: str, correlation_id: str | None):
    with connection() as conn:
        with UnitOfWork(conn):
            accounts = _accounts(conn, payment_id)
            lifecycle = PaymentLifecycle(conn, MockProvider())
            try:
                if operation == "capture":
                    result = lifecycle.capture(payment_id=payment_id, amount=Decimal(amount.amount), currency=amount.currency.upper(),
                                               customer_ledger_account_id=accounts[0], clearing_ledger_account_id=accounts[1], correlation_id=correlation_id)
                elif operation == "void":
                    result = lifecycle.void(payment_id=payment_id, amount=Decimal(amount.amount), currency=amount.currency.upper(), correlation_id=correlation_id)
                else:
                    result = lifecycle.refund(payment_id=payment_id, amount=Decimal(amount.amount), currency=amount.currency.upper(),
                                              customer_ledger_account_id=accounts[0], clearing_ledger_account_id=accounts[1], correlation_id=correlation_id)
            except ValueError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            return {"payment_id": str(payment_id), "operation": operation.upper(), "status": result}


@router.post("/v1/payments/{payment_id}/capture", status_code=202)
def capture(payment_id: UUID, amount: LifecycleAmount, authorization: str | None = Header(default=None, alias="Authorization"), correlation_id: str | None = Header(default=None, alias="X-Correlation-ID")):
    return _run(payment_id, amount, "capture", correlation_id)


@router.post("/v1/payments/{payment_id}/void", status_code=202)
def void(payment_id: UUID, amount: LifecycleAmount, authorization: str | None = Header(default=None, alias="Authorization"), correlation_id: str | None = Header(default=None, alias="X-Correlation-ID")):
    return _run(payment_id, amount, "void", correlation_id)


@router.post("/v1/payments/{payment_id}/refund", status_code=202)
def refund(payment_id: UUID, amount: LifecycleAmount, authorization: str | None = Header(default=None, alias="Authorization"), correlation_id: str | None = Header(default=None, alias="X-Correlation-ID")):
    return _run(payment_id, amount, "refund", correlation_id)
