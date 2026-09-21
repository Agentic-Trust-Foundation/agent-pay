import os
from decimal import Decimal
from uuid import uuid4

import pytest

from agent_pay.db import connection
from agent_pay.ledger import post_journal
from agent_pay.outbox import enqueue


pytestmark = pytest.mark.integration


def test_postgres_double_entry_and_outbox():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests")

    with connection() as conn:
        with conn.transaction():
            currency = "USD"
            debit = conn.execute(
                """INSERT INTO ledger_accounts (currency, account_type, name)
                   VALUES (%s, 'CUSTOMER', %s) RETURNING id""",
                (currency, f"test-customer-{uuid4()}"),
            ).fetchone()[0]
            credit = conn.execute(
                """INSERT INTO ledger_accounts (currency, account_type, name)
                   VALUES (%s, 'CLEARING', %s) RETURNING id""",
                (currency, f"test-clearing-{uuid4()}"),
            ).fetchone()[0]

            journal_id = post_journal(
                conn,
                currency=currency,
                reference_type="TEST",
                reference_id=None,
                idempotency_key=f"test:{uuid4()}",
                correlation_id="test-correlation",
                postings=[
                    {
                        "ledger_account_id": debit,
                        "side": "DEBIT",
                        "amount": "12.50",
                        "currency": currency,
                    },
                    {
                        "ledger_account_id": credit,
                        "side": "CREDIT",
                        "amount": "12.50",
                        "currency": currency,
                    },
                ],
            )
            event_id = enqueue(
                conn,
                event_type="TestEvent",
                aggregate_type="journal",
                aggregate_id=journal_id,
                payload={"amount": "12.50"},
                correlation_id="test-correlation",
            )

            count = conn.execute(
                "SELECT count(*) FROM ledger_postings WHERE journal_id=%s", (journal_id,)
            ).fetchone()[0]
            assert count == 2
            assert (
                conn.execute(
                    "SELECT count(*) FROM outbox_events WHERE id=%s", (event_id,)
                ).fetchone()[0]
                == 1
            )
            totals = conn.execute(
                """SELECT side, sum(amount) FROM ledger_postings
                   WHERE journal_id=%s GROUP BY side ORDER BY side""",
                (journal_id,),
            ).fetchall()
            assert totals == [
                ("CREDIT", Decimal("12.5000")),
                ("DEBIT", Decimal("12.5000")),
            ]


def test_provider_operation_idempotency_key_cannot_change_payment_or_operation():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests")

    from agent_pay.repositories import PaymentRepository

    with connection() as conn:
        with conn.transaction():
            account_id = conn.execute(
                "INSERT INTO accounts (owner_reference) VALUES (%s) RETURNING id",
                (f"phase15-{uuid4()}",),
            ).fetchone()[0]
            agent_id = conn.execute(
                "INSERT INTO agents (account_id, name) VALUES (%s,%s) RETURNING id",
                (account_id, "phase15-agent"),
            ).fetchone()[0]
            request_one = conn.execute(
                """INSERT INTO payment_requests
                   (account_id, agent_id, amount, currency, purpose, idempotency_key)
                   VALUES (%s,%s,10,'USD','phase15',%s) RETURNING id""",
                (account_id, agent_id, f"phase15:req:{uuid4()}"),
            ).fetchone()[0]
            request_two = conn.execute(
                """INSERT INTO payment_requests
                   (account_id, agent_id, amount, currency, purpose, idempotency_key)
                   VALUES (%s,%s,20,'USD','phase15',%s) RETURNING id""",
                (account_id, agent_id, f"phase15:req:{uuid4()}"),
            ).fetchone()[0]
            payment_one = conn.execute(
                "INSERT INTO payments (payment_request_id, amount, currency, status) VALUES (%s,10,'USD','PROCESSING') RETURNING id",
                (request_one,),
            ).fetchone()[0]
            payment_two = conn.execute(
                "INSERT INTO payments (payment_request_id, amount, currency, status) VALUES (%s,20,'USD','PROCESSING') RETURNING id",
                (request_two,),
            ).fetchone()[0]

            repository = PaymentRepository(conn)
            key = f"phase15:operation:{uuid4()}"
            operation_id = repository.create_provider_operation(payment_one, "CAPTURE", key)
            assert repository.create_provider_operation(payment_one, "CAPTURE", key) == operation_id

            with pytest.raises(ValueError, match="idempotency key conflict"):
                repository.create_provider_operation(payment_one, "VOID", key)

            with pytest.raises(ValueError, match="idempotency key conflict"):
                repository.create_provider_operation(payment_two, "CAPTURE", key)
