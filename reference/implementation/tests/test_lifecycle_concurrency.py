import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from uuid import uuid4

import pytest

from agent_pay.db import connection
from agent_pay.lifecycle import PaymentLifecycle
from agent_pay.provider import MockProvider, ProviderOutcome


pytestmark = pytest.mark.integration


def _setup_captured_payment(conn):
    account_id = conn.execute(
        "INSERT INTO accounts (owner_reference) VALUES (%s) RETURNING id", (f"refund-{uuid4()}",)
    ).fetchone()[0]
    wallet_id = conn.execute(
        "INSERT INTO wallets (account_id, currency, balance, available_balance) VALUES (%s,'USD',100,100) RETURNING id",
        (account_id,),
    ).fetchone()[0]
    customer = conn.execute(
        "INSERT INTO ledger_accounts (wallet_id,currency,account_type,name) VALUES (%s,'USD','CUSTOMER',%s) RETURNING id",
        (wallet_id, f"customer-{uuid4()}"),
    ).fetchone()[0]
    clearing = conn.execute(
        "INSERT INTO ledger_accounts (currency,account_type,name) VALUES ('USD','CLEARING',%s) RETURNING id",
        (f"clearing-{uuid4()}",),
    ).fetchone()[0]
    agent = conn.execute(
        "INSERT INTO agents (account_id,name) VALUES (%s,'refund-agent') RETURNING id", (account_id,)
    ).fetchone()[0]
    request = conn.execute(
        """INSERT INTO payment_requests (account_id,agent_id,amount,currency,purpose,idempotency_key)
           VALUES (%s,%s,100,'USD','purchase',%s) RETURNING id""",
        (account_id, agent, f"refund:{uuid4()}"),
    ).fetchone()[0]
    payment = conn.execute(
        "INSERT INTO payments (payment_request_id,amount,currency,status) VALUES (%s,100,'USD','SUCCEEDED') RETURNING id",
        (request,),
    ).fetchone()[0]
    capture = conn.execute(
        """INSERT INTO transactions
           (payment_id,type,status,amount,currency,idempotency_key,posted_at)
           VALUES (%s,'CAPTURE','POSTED',100,'USD',%s,now()) RETURNING id""",
        (payment, f"capture:{payment}"),
    ).fetchone()[0]
    return payment, customer, clearing, capture


def test_concurrent_refunds_never_exceed_captured_amount():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests")

    with connection() as setup_conn:
        with setup_conn.transaction():
            payment_id, customer, clearing, _ = _setup_captured_payment(setup_conn)

    def refund_once():
        with connection() as conn:
            lifecycle = PaymentLifecycle(conn, MockProvider(outcome=ProviderOutcome.SUCCEEDED))
            try:
                with conn.transaction():
                    result = lifecycle.refund(
                        payment_id=payment_id,
                        amount=Decimal("60.00"),
                        currency="USD",
                        customer_ledger_account_id=customer,
                        clearing_ledger_account_id=clearing,
                        correlation_id="concurrent-refund",
                    )
                    return result
            except ValueError:
                return "REJECTED"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: refund_once(), range(2)))

    assert results.count("REFUNDED") == 1
    assert results.count("REJECTED") == 1

    with connection() as conn:
        refunded = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE payment_id=%s AND type='REFUND' AND status='POSTED'",
            (payment_id,),
        ).fetchone()[0]
        assert Decimal(str(refunded)) == Decimal("60.00")


def test_concurrent_capture_and_void_are_mutually_exclusive():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests")

    with connection() as setup_conn:
        with setup_conn.transaction():
            account_id = setup_conn.execute(
                "INSERT INTO accounts (owner_reference) VALUES (%s) RETURNING id", (f"capture-void-{uuid4()}",)
            ).fetchone()[0]
            agent = setup_conn.execute(
                "INSERT INTO agents (account_id,name) VALUES (%s,'capture-void-agent') RETURNING id", (account_id,)
            ).fetchone()[0]
            request = setup_conn.execute(
                """INSERT INTO payment_requests (account_id,agent_id,amount,currency,purpose,idempotency_key)
                   VALUES (%s,%s,100,'USD','purchase',%s) RETURNING id""",
                (account_id, agent, f"capture-void:{uuid4()}"),
            ).fetchone()[0]
            payment_id = setup_conn.execute(
                "INSERT INTO payments (payment_request_id,amount,currency,status) VALUES (%s,100,'USD','AUTHORIZED') RETURNING id",
                (request,),
            ).fetchone()[0]
            wallet = setup_conn.execute(
                "INSERT INTO wallets (account_id,currency,balance,available_balance) VALUES (%s,'USD',100,100) RETURNING id",
                (account_id,),
            ).fetchone()[0]
            customer = setup_conn.execute(
                "INSERT INTO ledger_accounts (wallet_id,currency,account_type,name) VALUES (%s,'USD','CUSTOMER',%s) RETURNING id",
                (wallet, f"customer-{uuid4()}"),
            ).fetchone()[0]
            clearing = setup_conn.execute(
                "INSERT INTO ledger_accounts (currency,account_type,name) VALUES ('USD','CLEARING',%s) RETURNING id",
                (f"clearing-{uuid4()}",),
            ).fetchone()[0]

    def capture_once():
        with connection() as conn:
            with conn.transaction():
                return PaymentLifecycle(conn, MockProvider()).capture(
                    payment_id=payment_id, amount=Decimal("100"), currency="USD",
                    customer_ledger_account_id=customer, clearing_ledger_account_id=clearing,
                )

    def void_once():
        with connection() as conn:
            with conn.transaction():
                return PaymentLifecycle(conn, MockProvider()).void(
                    payment_id=payment_id, amount=Decimal("100"), currency="USD"
                )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(capture_once), pool.submit(void_once)]
        results = []
        for future in futures:
            try:
                results.append(future.result())
            except ValueError as exc:
                results.append(str(exc))

    assert sum(result == "SUCCEEDED" for result in results) + sum(result == "VOIDED" for result in results) == 1
