import os
from decimal import Decimal
from uuid import uuid4

import psycopg

from agent_pay.db import connection
from agent_pay.ledger import post_journal
from agent_pay.outbox import enqueue


pytestmark = []


def test_postgres_double_entry_and_outbox():
    if not os.getenv("DATABASE_URL"):
        return

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
                    {"ledger_account_id": debit, "side": "DEBIT", "amount": "12.50", "currency": currency},
                    {"ledger_account_id": credit, "side": "CREDIT", "amount": "12.50", "currency": currency},
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
            assert conn.execute("SELECT count(*) FROM outbox_events WHERE id=%s", (event_id,)).fetchone()[0] == 1
            totals = conn.execute(
                """SELECT side, sum(amount) FROM ledger_postings
                   WHERE journal_id=%s GROUP BY side ORDER BY side""",
                (journal_id,),
            ).fetchall()
            assert totals == [("CREDIT", Decimal("12.5000")), ("DEBIT", Decimal("12.5000"))]
