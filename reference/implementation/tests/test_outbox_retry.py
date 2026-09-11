import os
from uuid import uuid4

import pytest

from agent_pay.db import connection
from agent_pay.outbox import claim_batch, enqueue, mark_failed, mark_published


pytestmark = pytest.mark.integration


def test_outbox_publication_failure_is_retryable_without_losing_event():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests")

    with connection() as conn:
        with conn.transaction():
            aggregate_id = conn.execute(
                "INSERT INTO accounts (owner_reference) VALUES (%s) RETURNING id",
                (f"outbox-{uuid4()}",),
            ).fetchone()[0]
            event_id = enqueue(
                conn,
                event_type="PaymentSucceeded",
                aggregate_type="payment",
                aggregate_id=aggregate_id,
                payload={"payment_id": str(aggregate_id)},
                correlation_id="outbox-retry-test",
            )

        with conn.transaction():
            claimed = claim_batch(conn, 10)
            assert len(claimed) == 1
            assert claimed[0][0] == event_id
            assert claimed[0][-1] == 1
            mark_failed(conn, event_id, retry_after_seconds=0)

        with conn.transaction():
            claimed_again = claim_batch(conn, 10)
            assert len(claimed_again) == 1
            assert claimed_again[0][0] == event_id
            assert claimed_again[0][-1] == 2
            mark_published(conn, event_id)

        row = conn.execute(
            "SELECT status, attempts, published_at FROM outbox_events WHERE id=%s",
            (event_id,),
        ).fetchone()
        assert row[0] == "PUBLISHED"
        assert row[1] == 2
        assert row[2] is not None


def test_outbox_commit_is_atomic_with_business_transaction():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests")

    with connection() as conn:
        account_id = conn.execute(
            "INSERT INTO accounts (owner_reference) VALUES (%s) RETURNING id",
            (f"outbox-atomic-{uuid4()}",),
        ).fetchone()[0]
        try:
            with conn.transaction():
                event_id = enqueue(
                    conn,
                    event_type="PaymentStarted",
                    aggregate_type="account",
                    aggregate_id=account_id,
                    payload={"account_id": str(account_id)},
                )
                raise RuntimeError("simulate business transaction failure")
        except RuntimeError:
            pass

        assert conn.execute(
            "SELECT 1 FROM outbox_events WHERE id=%s", (event_id,)
        ).fetchone() is None
