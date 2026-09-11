import os

import pytest

from agent_pay.db import connection


pytestmark = pytest.mark.integration


def test_clean_database_has_required_stage4_tables():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests")

    required = {
        "authorization_evidence",
        "policy_versions",
        "budget_reservations",
        "payment_authentications",
        "provider_operations",
        "provider_events",
        "settlements",
        "reconciliation_records",
        "outbox_events",
        "ledger_journals",
        "ledger_postings",
    }
    with connection() as conn:
        rows = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name = ANY(%s)",
            (list(required),),
        ).fetchall()
    assert {row[0] for row in rows} == required
