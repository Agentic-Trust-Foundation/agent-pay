"""HTTP provider webhook and settlement ingestion boundary.

Provider input is untrusted. Signature verification happens before parsing or
financial mutation. Financial resolution remains inside the PostgreSQL-backed
resolver and settlement repository.
"""
import json
import os
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request

from .db import connection
from .lifecycle_api import router as lifecycle_router
from .provider_events import ProviderEventRepository, verify_hmac_signature
from .settlement import SettlementRepository
from .unit_of_work import UnitOfWork
from .webhook_resolution import ProviderEventResolver

router = APIRouter(tags=["providers"])
router.include_router(lifecycle_router)


def _secret_for(provider_name: str) -> str:
    key = "AGENT_PAY_PROVIDER_WEBHOOK_SECRET_" + "".join(
        c if c.isalnum() else "_" for c in provider_name.upper()
    )
    return os.getenv(key) or os.getenv("AGENT_PAY_PROVIDER_WEBHOOK_SECRET", "")


def _enforce_replay_window(payload: dict) -> None:
    raw_window = os.getenv("AGENT_PAY_WEBHOOK_REPLAY_WINDOW_SECONDS", "0")
    try:
        window = int(raw_window)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="invalid webhook replay-window configuration") from exc
    if window <= 0:
        return
    occurred_at = payload.get("occurred_at") or payload.get("timestamp")
    if not isinstance(occurred_at, str):
        raise HTTPException(status_code=400, detail="provider timestamp is required")
    try:
        parsed = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid provider timestamp") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    age = abs((datetime.now(timezone.utc) - parsed).total_seconds())
    if age > window:
        raise HTTPException(status_code=400, detail="provider event is outside replay window")


def _ledger_accounts(conn, payment_id: UUID):
    row = conn.execute(
        """SELECT la.id,
                  (SELECT ppa.ledger_account_id
                     FROM payment_provider_accounts ppa
                    WHERE ppa.provider_name=%s
                      AND ppa.currency=p.currency
                      AND ppa.status='ACTIVE')
             FROM payments p
             JOIN payment_requests pr ON pr.id=p.payment_request_id
             JOIN wallets w ON w.account_id=pr.account_id
                  AND w.currency=p.currency AND w.status='ACTIVE'
             JOIN ledger_accounts la ON la.wallet_id=w.id
            WHERE p.id=%s
            LIMIT 1""",
        ("mock", payment_id),
    ).fetchone()
    if not row or not row[0] or not row[1]:
        raise HTTPException(status_code=409, detail="ledger accounts are not configured")
    return UUID(str(row[0])), UUID(str(row[1]))


@router.post("/v1/providers/{provider_name}/webhooks")
async def provider_webhook(
    provider_name: str,
    request: Request,
    x_provider_signature: str | None = Header(default=None, alias="X-Provider-Signature"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-ID"),
):
    body = await request.body()
    secret = _secret_for(provider_name)
    if not secret or not x_provider_signature or not verify_hmac_signature(body, x_provider_signature, secret):
        raise HTTPException(status_code=401, detail="invalid provider signature")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid JSON payload") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="provider payload must be an object")
    _enforce_replay_window(payload)
    event_id = payload.get("event_id")
    event_type = payload.get("event_type")
    provider_reference = payload.get("provider_reference")
    if not isinstance(event_id, str) or not isinstance(event_type, str):
        raise HTTPException(status_code=400, detail="event_id and event_type are required")

    outcome_map = {"payment.succeeded": "SUCCEEDED", "payment.failed": "FAILED"}
    outcome = outcome_map.get(event_type)

    with connection() as conn:
        with UnitOfWork(conn):
            event_repo = ProviderEventRepository(conn)
            event_db_id = event_repo.record(
                provider_name=provider_name, event_id=event_id, event_type=event_type,
                payload=payload, signature_valid=True,
            )
            if event_db_id is None:
                return {"status": "DUPLICATE", "event_id": event_id}
            if not outcome:
                return {"status": "ACCEPTED", "event_id": event_id}
            if not isinstance(provider_reference, str) or not provider_reference:
                raise HTTPException(status_code=400, detail="provider_reference is required for financial events")
            operation = conn.execute(
                """SELECT id, payment_id FROM provider_operations
                   WHERE provider_reference=%s ORDER BY created_at DESC LIMIT 1 FOR UPDATE""",
                (provider_reference,),
            ).fetchone()
            if not operation:
                raise HTTPException(status_code=404, detail="provider operation not found")
            conn.execute(
                "UPDATE provider_events SET provider_operation_id=%s WHERE id=%s",
                (operation[0], event_db_id),
            )
            customer_account, clearing_account = _ledger_accounts(conn, UUID(str(operation[1])))
            result = ProviderEventResolver(conn).resolve(
                event_id=event_db_id, provider_operation_id=operation[0], outcome=outcome,
                provider_reference=provider_reference, customer_ledger_account_id=customer_account,
                clearing_ledger_account_id=clearing_account, correlation_id=x_correlation_id,
            )
            return {"status": result, "event_id": event_id, "payment_id": str(operation[1])}


@router.post("/v1/providers/{provider_name}/settlements")
async def provider_settlement(
    provider_name: str,
    request: Request,
    x_provider_signature: str | None = Header(default=None, alias="X-Provider-Signature"),
):
    body = await request.body()
    secret = _secret_for(provider_name)
    if not secret or not x_provider_signature or not verify_hmac_signature(body, x_provider_signature, secret):
        raise HTTPException(status_code=401, detail="invalid provider signature")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid JSON payload") from exc
    required = ("settlement_reference", "provider_reference", "amount", "currency")
    if any(not isinstance(payload.get(key), str) or not payload[key] for key in required):
        raise HTTPException(status_code=400, detail="settlement_reference, provider_reference, amount and currency are required")
    with connection() as conn:
        result = SettlementRepository(conn).ingest(
            provider_name=provider_name,
            settlement_reference=payload["settlement_reference"],
            provider_reference=payload["provider_reference"],
            observed_amount=payload["amount"],
            observed_currency=payload["currency"],
            reported_at=payload.get("reported_at"), settled_at=payload.get("settled_at"),
        )
        return {"status": result, "settlement_reference": payload["settlement_reference"]}
