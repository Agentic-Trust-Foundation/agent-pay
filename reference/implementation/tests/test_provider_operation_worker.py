import os
from decimal import Decimal
from uuid import uuid4

import pytest
from psycopg.pq import TransactionStatus

from agent_pay.db import connection
from agent_pay.lifecycle import PaymentLifecycle
from agent_pay.provider import PaymentProvider, ProviderOutcome
from agent_pay.provider_worker import ProviderOperationWorker


pytestmark = pytest.mark.integration


class TransactionAwareProvider(PaymentProvider):
    def __init__(self, conn, outcome=ProviderOutcome.SUCCEEDED):
        self.conn = conn
        self.outcome = outcome
        self.calls = 0
        self.keys = []

    def _run(self, idempotency_key):
        assert self.conn.info.transaction_status == TransactionStatus.IDLE
        self.calls += 1
        self.keys.append(idempotency_key)
        return self.outcome

    def charge(self, payment_id, amount_minor, currency, idempotency_key):
        return self._run(idempotency_key)

    def capture(self, payment_id, amount_minor, currency, idempotency_key):
        return self._run(idempotency_key)

    def void(self, payment_id, amount_minor, currency, idempotency_key):
        return self._run(idempotency_key)

    def refund(self, payment_id, amount_minor, currency, idempotency_key):
        return self._run(idempotency_key)


def _payment(conn, status):
    account = conn.execute(
        "INSERT INTO accounts (owner_reference) VALUES (%s) RETURNING id",
        (f"worker-{uuid4()}",),
    ).fetchone()[0]
    agent = conn.execute(
        "INSERT INTO agents (account_id,name) VALUES (%s,'worker-agent') RETURNING id",
        (account,),
    ).fetchone()[0]
    request = conn.execute(
        """INSERT INTO payment_requests
           (account_id,agent_id,amount,currency,purpose,idempotency_key)
           VALUES (%s,%s,100,'USD','worker-test',%s) RETURNING id""",
        (account, agent, f"worker-request:{uuid4()}"),
    ).fetchone()[0]
    payment = conn.execute(
        """INSERT INTO payments
           (payment_request_id,amount,currency,status)
           VALUES (%s,100,'USD',%s) RETURNING id""",
        (request, status),
    ).fetchone()[0]
    wallet = conn.execute(
        """INSERT INTO wallets
           (account_id,currency,balance,available_balance)
           VALUES (%s,'USD',100,100) RETURNING id""",
        (account,),
    ).fetchone()[0]
    customer = conn.execute(
        """INSERT INTO ledger_accounts
           (wallet_id,currency,account_type,name)
           VALUES (%s,'USD','CUSTOMER',%s) RETURNING id""",
        (wallet, f"customer-{uuid4()}"),
    ).fetchone()[0]
    clearing = conn.execute(
        """INSERT INTO ledger_accounts
           (currency,account_type,name)
           VALUES ('USD','CLEARING',%s) RETURNING id""",
        (f"clearing-{uuid4()}",),
    ).fetchone()[0]
    return payment, request, customer, clearing


@pytest.mark.parametrize(
    ("operation", "initial_status", "expected"),
    [
        ("capture", "AUTHORIZED", "SUCCEEDED"),
        ("void", "AUTHORIZED", "VOIDED"),
    ],
)
def test_lifecycle_operations_execute_provider_outside_transaction(operation, initial_status, expected):
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests")

    with connection() as conn:
        with conn.transaction():
            payment, _, customer, clearing = _payment(conn, initial_status)
            lifecycle = PaymentLifecycle(conn, TransactionAwareProvider(conn))
            if operation == "capture":
                queued = lifecycle.capture(
                    payment_id=payment,
                    amount=Decimal("100"),
                    currency="USD",
                    customer_ledger_account_id=customer,
                    clearing_ledger_account_id=clearing,
                )
            else:
                queued = lifecycle.void(
                    payment_id=payment, amount=Decimal("100"), currency="USD"
                )
            assert queued in {"PROCESSING", "VOID_REQUESTED"}
            operation_id = conn.execute(
                "SELECT id FROM provider_operations WHERE payment_id=%s ORDER BY created_at DESC LIMIT 1",
                (payment,),
            ).fetchone()[0]

        provider = TransactionAwareProvider(conn)
        result = ProviderOperationWorker(conn, provider).run_once(
            operation_id=operation_id,
            customer_ledger_account_id=customer,
            clearing_ledger_account_id=clearing,
        )
        assert result == expected
        assert provider.calls == 1

        row = conn.execute(
            "SELECT status FROM payments WHERE id=%s", (payment,)
        ).fetchone()
        assert row[0] == expected


def test_refund_uses_persisted_partial_amount_and_finishes_in_worker():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests")

    with connection() as conn:
        with conn.transaction():
            payment, _, customer, clearing = _payment(conn, "SUCCEEDED")
            conn.execute(
                """INSERT INTO transactions
                   (payment_id,type,status,amount,currency,idempotency_key,posted_at)
                   VALUES (%s,'CAPTURE','POSTED',100,'USD',%s,now())""",
                (payment, f"tx:{payment}:capture"),
            )
            lifecycle = PaymentLifecycle(conn, TransactionAwareProvider(conn))
            assert lifecycle.refund(
                payment_id=payment,
                amount=Decimal("40.00"),
                currency="USD",
                customer_ledger_account_id=customer,
                clearing_ledger_account_id=clearing,
            ) == "REFUND_PROCESSING"

        provider = TransactionAwareProvider(conn)
        operation_id = conn.execute(
            "SELECT id FROM provider_operations WHERE payment_id=%s ORDER BY created_at DESC LIMIT 1",
            (payment,),
        ).fetchone()[0]
        assert ProviderOperationWorker(conn, provider).run_once(operation_id=operation_id) == "SUCCEEDED"
        assert provider.calls == 1

        tx = conn.execute(
            """SELECT amount,status FROM transactions
               WHERE payment_id=%s AND type='REFUND'""",
            (payment,),
        ).fetchone()
        assert Decimal(str(tx[0])) == Decimal("40.00")
        assert tx[1] == "POSTED"


def test_unknown_outcome_can_be_explicitly_retried_with_same_idempotency_key():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests")

    with connection() as conn:
        with conn.transaction():
            payment, _, customer, clearing = _payment(conn, "AUTHORIZED")
            lifecycle = PaymentLifecycle(conn, TransactionAwareProvider(conn, ProviderOutcome.UNKNOWN))
            assert lifecycle.capture(
                payment_id=payment,
                amount=Decimal("100"),
                currency="USD",
                customer_ledger_account_id=customer,
                clearing_ledger_account_id=clearing,
            ) == "PROCESSING"

        unknown_provider = TransactionAwareProvider(conn, ProviderOutcome.UNKNOWN)
        worker = ProviderOperationWorker(conn, unknown_provider)
        operation_id = conn.execute(
            "SELECT id FROM provider_operations WHERE payment_id=%s ORDER BY created_at DESC LIMIT 1",
            (payment,),
        ).fetchone()[0]
        assert worker.run_once(
            operation_id=operation_id,
            customer_ledger_account_id=customer,
            clearing_ledger_account_id=clearing,
        ) == "UNKNOWN_EXTERNAL_OUTCOME"

        operation = conn.execute(
            """SELECT id,status,idempotency_key
               FROM provider_operations WHERE payment_id=%s""",
            (payment,),
        ).fetchone()
        assert operation[1] == "UNKNOWN"

        assert worker.retry_unknown(operation[0]) is True

        success_provider = TransactionAwareProvider(conn, ProviderOutcome.SUCCEEDED)
        assert ProviderOperationWorker(conn, success_provider).run_once(
            operation_id=operation[0],
            customer_ledger_account_id=customer,
            clearing_ledger_account_id=clearing,
        ) == "SUCCEEDED"
        assert success_provider.keys == [operation[2]]
