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


def test_ledger_idempotency_replays_exact_journal_and_rejects_conflict():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests")

    key = f"ledger-idempotency:{uuid4()}"
    with connection() as conn:
        with conn.transaction():
            debit = conn.execute(
                """INSERT INTO ledger_accounts (currency, account_type, name)
                   VALUES ('USD', 'CUSTOMER', %s) RETURNING id""",
                (f"idem-debit-{uuid4()}",),
            ).fetchone()[0]
            credit = conn.execute(
                """INSERT INTO ledger_accounts (currency, account_type, name)
                   VALUES ('USD', 'CLEARING', %s) RETURNING id""",
                (f"idem-credit-{uuid4()}",),
            ).fetchone()[0]
            first = post_journal(
                conn,
                currency="USD",
                reference_type="TEST",
                reference_id=None,
                idempotency_key=key,
                correlation_id="idem",
                postings=[
                    {"ledger_account_id": debit, "side": "DEBIT", "amount": "20.00", "currency": "USD"},
                    {"ledger_account_id": credit, "side": "CREDIT", "amount": "20.00", "currency": "USD"},
                ],
            )

        assert post_journal(
            conn,
            currency="USD",
            reference_type="TEST",
            reference_id=None,
            idempotency_key=key,
            correlation_id="idem",
            postings=[
                {"ledger_account_id": debit, "side": "DEBIT", "amount": "20.00", "currency": "USD"},
                {"ledger_account_id": credit, "side": "CREDIT", "amount": "20.00", "currency": "USD"},
            ],
        ) == first

        with pytest.raises(ValueError, match="idempotency key conflict"):
            post_journal(
                conn,
                currency="USD",
                reference_type="TEST",
                reference_id=None,
                idempotency_key=key,
                correlation_id="idem",
                postings=[
                    {"ledger_account_id": debit, "side": "DEBIT", "amount": "21.00", "currency": "USD"},
                    {"ledger_account_id": credit, "side": "CREDIT", "amount": "21.00", "currency": "USD"},
                ],
            )


def test_database_rejects_unbalanced_ledger_journal_at_commit():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests")

    with connection() as conn:
        debit = conn.execute(
            """INSERT INTO ledger_accounts (currency, account_type, name)
               VALUES ('USD', 'CUSTOMER', %s) RETURNING id""",
            (f"trigger-debit-{uuid4()}",),
        ).fetchone()[0]
        with pytest.raises(Exception, match="ledger journal .* is not balanced"):
            with conn.transaction():
                journal_id = conn.execute(
                    """INSERT INTO ledger_journals
                       (currency, reference_type, idempotency_key)
                       VALUES ('USD', 'TEST', %s) RETURNING id""",
                    (f"unbalanced:{uuid4()}",),
                ).fetchone()[0]
                conn.execute(
                    """INSERT INTO ledger_postings
                       (journal_id, ledger_account_id, side, amount, currency)
                       VALUES (%s, %s, 'DEBIT', 10, 'USD')""",
                    (journal_id, debit),
                )
