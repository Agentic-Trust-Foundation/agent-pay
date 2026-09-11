import os
from uuid import uuid4

import pytest

from agent_pay.db import connection
from agent_pay.outbox import enqueue


pytestmark = pytest.mark.integration


def test_outbox_is_transactionally_atomic_with_database_commit():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests")

    with connection() as conn:
        with pytest.raises(RuntimeError):
            with conn.transaction():
                event_id = enqueue(
                    conn,
                    event_type="PaymentSucceeded",
                    aggregate_type="Payment",
                    aggregate_id=uuid4(),
                    payload={"test": True},
                )
                assert event_id
                raise RuntimeError("force rollback")

        count = conn.execute(
            "SELECT count(*) FROM outbox_events WHERE event_type='PaymentSucceeded' AND payload->>'test'='true'"
        ).fetchone()[0]
        assert count == 0

        with conn.transaction():
            event_id = enqueue(
                conn,
                event_type="PaymentSucceeded",
                aggregate_type="Payment",
                aggregate_id=uuid4(),
                payload={"test": "committed"},
            )
            assert event_id

        count = conn.execute(
            "SELECT count(*) FROM outbox_events WHERE event_type='PaymentSucceeded' AND payload->>'test'='committed'"
        ).fetchone()[0]
        assert count == 1
