"""Durable worker entrypoint for reserved payments.

The worker is intentionally separate from the API process. It claims a bounded
set of PROCESSING payments, resolves ledger accounts, and delegates external
execution to the payment worker primitive.
"""
import os
from uuid import UUID

from .db import connection
from .provider import MockProvider, ProviderOutcome
from .repositories import PaymentRepository
from .unit_of_work import UnitOfWork
from .worker import process_one


def run_once(limit: int = 25) -> int:
    with connection() as conn:
        with UnitOfWork(conn):
            rows = PaymentRepository(conn).pending_for_execution(limit)
            payment_ids = [row[0] for row in rows]

    provider = MockProvider(ProviderOutcome(os.getenv("AGENT_PAY_MOCK_OUTCOME", "SUCCEEDED")))
    processed = 0
    for payment_id in payment_ids:
        with connection() as conn:
            currency = _payment_currency(conn, payment_id)
            accounts = conn.execute(
                """SELECT la.id,
                          (SELECT ppa.ledger_account_id FROM payment_provider_accounts ppa
                           WHERE ppa.provider_name=%s AND ppa.currency=%s AND ppa.status='ACTIVE')
                   FROM payments p
                   JOIN payment_requests pr ON pr.id=p.payment_request_id
                   JOIN wallets w ON w.account_id=pr.account_id AND w.currency=p.currency AND w.status='ACTIVE'
                   JOIN ledger_accounts la ON la.wallet_id=w.id
                   WHERE p.id=%s LIMIT 1""",
                ("mock", currency, payment_id),
            ).fetchone()
            if not accounts or not accounts[0] or not accounts[1]:
                raise RuntimeError("customer wallet ledger account or provider clearing account is missing")
            process_one(
                conn=conn, payment_id=UUID(str(payment_id)), provider=provider,
                customer_ledger_account_id=UUID(str(accounts[0])),
                clearing_ledger_account_id=UUID(str(accounts[1])),
            )
            processed += 1
    return processed


def _payment_currency(conn, payment_id: UUID) -> str:
    row = conn.execute("SELECT currency FROM payments WHERE id=%s", (payment_id,)).fetchone()
    if not row:
        raise ValueError("payment not found")
    return row[0].strip().upper()


if __name__ == "__main__":
    print(f"processed={run_once()}")
