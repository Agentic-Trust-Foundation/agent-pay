"""FastAPI surface for the PostgreSQL-backed reference implementation."""
import hashlib
import json
from decimal import Decimal
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .auth import require_agent, resolve_approval_bearer, resolve_bearer
from .control import ControlRepository
from .db import connection
from .orchestrator import PaymentOrchestrator
from .outbox import enqueue
from .provider import MockProvider
from .repositories import PaymentRepository
from .unit_of_work import UnitOfWork

app = FastAPI(title="Agent-Pay Reference", version="0.3.0")


class Money(BaseModel):
    value: str = Field(pattern=r"^\d+(\.\d{1,4})?$")
    currency: str = Field(min_length=3, max_length=3)


class Merchant(BaseModel):
    name: str
    domain: str | None = None
    category: str | None = None


class PaymentItem(BaseModel):
    name: str
    quantity: int = Field(gt=0)
    unit_price: str = Field(pattern=r"^\d+(\.\d{1,4})?$")


class CreatePayment(BaseModel):
    agent_id: UUID
    account_id: UUID
    policy_id: UUID | None = None
    budget_id: UUID | None = None
    merchant: Merchant | None = None
    amount: Money
    purpose: str = Field(min_length=1, max_length=500)
    items: list[PaymentItem] = Field(default_factory=list)


class ApprovalDecision(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


def request_fingerprint(request: CreatePayment) -> str:
    canonical = json.dumps(request.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def _authenticate_agent(authorization: str | None, request: CreatePayment) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer authentication is required")
    try:
        principal = resolve_bearer(authorization[7:].strip())
        require_agent(principal, str(request.agent_id), str(request.account_id))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _policy_id(conn, policy_version_id: UUID):
    row = conn.execute("SELECT policy_id FROM policy_versions WHERE id=%s", (policy_version_id,)).fetchone()
    return row[0] if row else None


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/v1/payments", status_code=202)
def create_payment(
    request: CreatePayment,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-ID"),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    if not idempotency_key or not idempotency_key.strip():
        raise HTTPException(status_code=400, detail="Idempotency-Key is required")
    if len(idempotency_key) > 255:
        raise HTTPException(status_code=400, detail="Idempotency-Key is too long")
    _authenticate_agent(authorization, request)
    fingerprint = request_fingerprint(request)
    deferred_error = None

    with connection() as conn:
        with UnitOfWork(conn):
            repo = PaymentRepository(conn)
            control = ControlRepository(conn)
            existing = repo.find_by_idempotency(request.account_id, idempotency_key)
            if existing:
                if existing[5] and existing[5] != fingerprint:
                    raise HTTPException(status_code=409, detail="idempotency key was already used with a different payment request")
                payment = conn.execute("SELECT id, status FROM payments WHERE payment_request_id=%s", (existing[0],)).fetchone()
                if payment:
                    return {"payment_id": str(payment[0]), "status": payment[1]}
                raise HTTPException(status_code=409, detail="idempotency key already belongs to an incomplete request")

            merchant_id = None
            if request.merchant:
                merchant_id = repo.merchant(name=request.merchant.name, domain=request.merchant.domain)
            currency = request.amount.currency.upper()
            request_id = repo.create_request(
                account_id=request.account_id, agent_id=request.agent_id, amount=request.amount.value,
                currency=currency, purpose=request.purpose, items=[i.model_dump() for i in request.items],
                idempotency_key=idempotency_key, request_fingerprint=fingerprint, merchant_id=merchant_id,
            )
            payment_id = repo.create_payment(request_id=request_id, amount=request.amount.value,
                                             currency=currency, status="POLICY_CHECK")
            domain = request.merchant.domain if request.merchant and request.merchant.domain else ""
            category = request.merchant.category if request.merchant else None
            try:
                decision, version_id, _ = control.evaluate_policy(
                    account_id=request.account_id, policy_id=request.policy_id,
                    payment_request_id=request_id, agent_id=request.agent_id, payment_id=payment_id,
                    amount=Decimal(request.amount.value), currency=currency,
                    merchant_domain=domain, category=category,
                )
            except LookupError as exc:
                deferred_error = (403, str(exc), "POLICY_NOT_CONFIGURED")
            else:
                if decision.value == "DENY":
                    repo.update_status(payment_id, "FAILED")
                    enqueue(conn, event_type="PaymentFailed", aggregate_type="payment", aggregate_id=payment_id,
                            payload={"reason": "POLICY_DENIED", "policy_version_id": str(version_id)}, correlation_id=correlation_id)
                    deferred_error = (403, "payment denied by policy", "POLICY_DENIED")
                elif decision.value == "REQUIRE_APPROVAL":
                    approval_id = control.create_approval(request_id, reason="policy requires approval")
                    repo.update_status(payment_id, "APPROVAL_REQUIRED")
                    enqueue(conn, event_type="ApprovalRequested", aggregate_type="payment", aggregate_id=payment_id,
                            payload={"approval_id": str(approval_id), "policy_version_id": str(version_id)}, correlation_id=correlation_id)
                    return {"payment_id": str(payment_id), "status": "APPROVAL_REQUIRED", "approval_id": str(approval_id), "correlation_id": correlation_id}
                else:
                    policy_id = _policy_id(conn, version_id)
                    budget_id = control.select_budget(request.account_id, request.budget_id, currency, policy_id)
                    if not budget_id:
                        repo.update_status(payment_id, "FAILED")
                        enqueue(conn, event_type="PaymentFailed", aggregate_type="payment", aggregate_id=payment_id,
                                payload={"reason": "BUDGET_UNAVAILABLE", "policy_version_id": str(version_id)}, correlation_id=correlation_id)
                        deferred_error = (409, "exactly one active compatible budget is required", "BUDGET_UNAVAILABLE")
                    else:
                        orchestrator = PaymentOrchestrator(conn, MockProvider())
                        orchestrator.prepare(payment_id=payment_id, payment_request_id=request_id, budget_id=budget_id,
                                             amount=Decimal(request.amount.value), currency=currency,
                                             correlation_id=correlation_id)
                        if decision.value == "ALLOW_NOTIFY":
                            enqueue(conn, event_type="NotificationRequested", aggregate_type="payment", aggregate_id=payment_id,
                                    payload={"type": "PAYMENT_EXECUTION", "amount": request.amount.value, "currency": currency},
                                    correlation_id=correlation_id)
                        return {"payment_id": str(payment_id), "status": "PROCESSING", "decision": decision.value, "correlation_id": correlation_id}

    if deferred_error:
        status, message, _ = deferred_error
        raise HTTPException(status_code=status, detail=message)
    raise HTTPException(status_code=409, detail="payment could not be prepared")


@app.post("/v1/approvals/{approval_id}/approve", status_code=202)
def approve_payment(
    approval_id: UUID,
    decision: ApprovalDecision | None = None,
    authorization: str | None = Header(default=None, alias="Authorization"),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-ID"),
):
    token = authorization[7:].strip() if authorization and authorization.startswith("Bearer ") else None
    try:
        actor = resolve_approval_bearer(token)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    with connection() as conn:
        with UnitOfWork(conn):
            control = ControlRepository(conn)
            approval = control.get_approval(approval_id)
            if not approval:
                raise HTTPException(status_code=404, detail="approval not found")
            if approval[2] != "PENDING":
                raise HTTPException(status_code=409, detail="approval is no longer pending")
            req = control.payment_request(approval[1])
            if not req:
                raise HTTPException(status_code=404, detail="payment request not found")
            policy_id = _policy_id(conn, req[7]) if req[7] else None
            if not policy_id:
                raise HTTPException(status_code=409, detail="payment has no valid policy version")
            budget_id = control.select_budget(req[1], None, req[4].strip().upper(), policy_id)
            if not budget_id:
                raise HTTPException(status_code=409, detail="exactly one active compatible budget is required")
            control.set_approval(approval_id, "APPROVED", actor, decision.reason if decision else None)
            orchestrator = PaymentOrchestrator(conn, MockProvider())
            orchestrator.prepare(payment_id=req[9], payment_request_id=req[0], budget_id=budget_id,
                                 amount=Decimal(str(req[3])), currency=req[4].strip().upper(),
                                 correlation_id=correlation_id)
            enqueue(conn, event_type="PaymentApproved", aggregate_type="payment", aggregate_id=req[9],
                    payload={"approval_id": str(approval_id), "approved_by": actor}, correlation_id=correlation_id)
            return {"payment_id": str(req[9]), "approval_id": str(approval_id), "status": "PROCESSING", "correlation_id": correlation_id}


@app.post("/v1/approvals/{approval_id}/deny", status_code=202)
def deny_payment(
    approval_id: UUID,
    decision: ApprovalDecision | None = None,
    authorization: str | None = Header(default=None, alias="Authorization"),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-ID"),
):
    token = authorization[7:].strip() if authorization and authorization.startswith("Bearer ") else None
    try:
        actor = resolve_approval_bearer(token)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    with connection() as conn:
        with UnitOfWork(conn):
            control = ControlRepository(conn)
            approval = control.get_approval(approval_id)
            if not approval:
                raise HTTPException(status_code=404, detail="approval not found")
            if approval[2] != "PENDING":
                raise HTTPException(status_code=409, detail="approval is no longer pending")
            req = control.payment_request(approval[1])
            control.set_approval(approval_id, "DENIED", actor, decision.reason if decision else None)
            PaymentRepository(conn).update_status(req[9], "FAILED")
            enqueue(conn, event_type="PaymentFailed", aggregate_type="payment", aggregate_id=req[9],
                    payload={"reason": "USER_DENIED", "approval_id": str(approval_id)}, correlation_id=correlation_id)
            return {"payment_id": str(req[9]), "approval_id": str(approval_id), "status": "FAILED", "correlation_id": correlation_id}


@app.get("/v1/payments/{payment_id}")
def get_payment(payment_id: UUID):
    with connection() as conn:
        row = PaymentRepository(conn).get_payment(payment_id)
        if not row:
            raise HTTPException(status_code=404, detail="payment not found")
        return {"payment_id": str(row[0]), "payment_request_id": str(row[1]), "amount": str(row[2]),
                "currency": row[3].strip(), "status": row[4], "provider_reference": row[5]}
