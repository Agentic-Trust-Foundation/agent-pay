import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from uuid import uuid4

import pytest

from agent_pay.db import connection
from agent_pay.repositories import BudgetRepository


pytestmark = pytest.mark.integration


def test_concurrent_budget_reservations_are_serialized():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests")

    with connection() as conn:
        with conn.transaction():
            account_id = conn.execute(
                "INSERT INTO accounts (owner_reference) VALUES (%s) RETURNING id",
                (f"budget-race-{uuid4()}",),
            ).fetchone()[0]
            agent_id = conn.execute(
                "INSERT INTO agents (account_id, name) VALUES (%s,%s) RETURNING id",
                (account_id, "budget-race-agent"),
            ).fetchone()[0]
            policy_id = conn.execute(
                "INSERT INTO policies (account_id, name, rules) VALUES (%s,%s,%s::jsonb) RETURNING id",
                (account_id, f"budget-race-policy-{uuid4()}", '{"limits":{"per_transaction":100}}'),
            ).fetchone()[0]
            budget_id = conn.execute(
                """INSERT INTO budgets
                   (account_id, policy_id, name, currency, limit_amount)
                   VALUES (%s,%s,%s,'USD',100) RETURNING id""",
                (account_id, policy_id, f"budget-race-{uuid4()}"),
            ).fetchone()[0]
            request_ids = []
            for _ in range(2):
                request_ids.append(
                    conn.execute(
                        """INSERT INTO payment_requests
                           (account_id, agent_id, amount, currency, purpose, idempotency_key)
                           VALUES (%s,%s,60,'USD','concurrent reservation',%s) RETURNING id""",
                        (account_id, agent_id, f"budget-race:{uuid4()}"),
                    ).fetchone()[0]
                )

    def reserve(request_id):
        with connection() as conn:
            with conn.transaction():
                return BudgetRepository(conn).reserve(
                    budget_id, request_id, "60.00"
                )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.map(reserve, request_ids)

    assert sorted(result is not None for result in (first, second)) == [False, True]

    with connection() as conn:
        budget = conn.execute(
            "SELECT consumed_amount, reserved_amount FROM budgets WHERE id=%s",
            (budget_id,),
        ).fetchone()
        reservations = conn.execute(
            "SELECT count(*) FROM budget_reservations WHERE budget_id=%s AND status='RESERVED'",
            (budget_id,),
        ).fetchone()[0]

    assert budget == (Decimal("0.0000"), Decimal("60.0000"))
    assert reservations == 1
