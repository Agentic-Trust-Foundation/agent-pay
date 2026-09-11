"""FastAPI surface for the PostgreSQL-backed reference implementation."""
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .db import connection
from .repositories import PaymentRepository
from .unit_of_work import UnitOfWork

app = FastAPI(title="Agent-Pay Reference", version="0.2.0")


class Money(BaseModel):
    value: str = Field(pattern=r"^\d+(\.\d{1,4})?$")
    currency: str = Field(min_length=3, max_length=3)


class Merchant(BaseModel):
    name: str
    domain: str | None = None


class PaymentItem(BaseModel):
    name: str
    quantity: int = Field(gt=0)
    unit_price: str


class CreatePayment(BaseModel):
    agent_id: UUID
    account_id: UUID
    merchant: Merchant | None = None
    amount: Money
    purpose: str
    items: list[PaymentItem] = []


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/v1/payments", status_code=202)
def create_payment(request: CreatePayment, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
                   correlation_id: str | None = Header(default=None, alias="X-Correlation-ID")):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key is required")
    with connection() as conn:
        with UnitOfWork(conn):
            repo = PaymentRepository(conn)
            existing = repo.find_by_idempotency(request.account_id, idempotency_key)
            if existing:
                payment = conn.execute(
                    "SELECT id, status FROM payments WHERE payment_request_id=%s", (existing[0],)
                ).fetchone()
                if payment:
                    return {"payment_id": str(payment[0]), "status": payment[1]}
                raise HTTPException(status_code=409, detail="idempotency key already belongs to an incomplete request")
            request_id = repo.create_request(
                account_id=request.account_id,
                agent_id=request.agent_id,
                amount=request.amount.value,
                currency=request.amount.currency.upper(),
                purpose=request.purpose,
                items=[i.model_dump() for i in request.items],
                idempotency_key=idempotency_key,
            )
            # Provider execution is intentionally outside this API transaction in the next
            # execution layer. V1 persists the intent first and returns a pending payment.
            payment_id = repo.create_payment(
                request_id=request_id,
                amount=request.amount.value,
                currency=request.amount.currency.upper(),
                status="PAYMENT_PENDING",
            )
            return {"payment_id": str(payment_id), "status": "PAYMENT_PENDING", "correlation_id": correlation_id}


@app.get("/v1/payments/{payment_id}")
def get_payment(payment_id: UUID):
    with connection() as conn:
        row = PaymentRepository(conn).get_payment(payment_id)
        if not row:
            raise HTTPException(status_code=404, detail="payment not found")
        return {"payment_id": str(row[0]), "payment_request_id": str(row[1]), "amount": str(row[2]),
                "currency": row[3], "status": row[4], "provider_reference": row[5]}
