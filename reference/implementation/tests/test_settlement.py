import os
from uuid import uuid4

from agent_pay.db import connection
from agent_pay.settlement import SettlementRepository


def _fixture(conn, *, amount="25.00", currency="USD", provider_status="SUCCEEDED"):
    account_id = conn.execute(
        "INSERT INTO accounts (owner_reference) VALUES (%s) RETURNING id",
        (f"settlement-test-{uuid4()}",),
    ).fetchone()[0]
    agent_id = conn.execute(
        "INSERT INTO agents (account_id, name) VALUES (%s,%s) RETURNING id",
        (account_id, "settlement-test-agent"),
    ).fetchone()[0]
    request_id = conn.execute(
        """INSERT INTO payment_requests
           (account_id, agent_id, amount, currency, purpose, idempotency_key)
           VALUES (%s,%s,%s,%s,'purchase',%s) RETURNING id""",
        (account_id, agent_id, amount, currency, f"settlement:{uuid4()}"),
    ).fetchone()[0]
    payment_id = conn.execute(
        """INSERT INTO payments (payment_request_id, amount, currency, status)
           VALUES (%s,%s,%s,'SUCCEEDED') RETURNING id""",
        (request_id, amount, currency),
    ).fetchone()[0]
    provider_reference = f"prov_{uuid4()}"
    operation_id = conn.execute(
        """INSERT INTO provider_operations
           (payment_id, operation_type, idempotency_key, provider_reference, status)
           VALUES (%s,'CHARGE',%s,%s,%s) RETURNING id""",
        (payment_id, f"charge:{uuid4()}", provider_reference, provider_status),
    ).fetchone()[0]
    return operation_id, provider_reference


def test_settlement_matches_provider_operation():
    if not os.getenv("DATABASE_URL"):
        return
    with connection() as conn:
        with conn.transaction():
            operation_id, provider_reference = _fixture(conn)
        result = SettlementRepository(conn).ingest(
            provider_name="mock", settlement_reference=f"settle_{uuid4()}",
            provider_reference=provider_reference, observed_amount="25.00", observed_currency="usd",
        )
        assert result == "MATCHED"
        row = conn.execute(
            """SELECT rr.status, rr.discrepancy_code, rr.provider_operation_id
               FROM reconciliation_records rr WHERE rr.provider_operation_id=%s""", (operation_id,)
        ).fetchone()
        assert row == ("MATCHED", None, operation_id)


def test_settlement_amount_mismatch_does_not_mutate_payment():
    if not os.getenv("DATABASE_URL"):
        return
    with connection() as conn:
        with conn.transaction():
            operation_id, provider_reference = _fixture(conn)
            payment_status = conn.execute(
                "SELECT p.status FROM payments p JOIN provider_operations po ON po.payment_id=p.id WHERE po.id=%s",
                (operation_id,),
            ).fetchone()[0]
        result = SettlementRepository(conn).ingest(
            provider_name="mock", settlement_reference=f"settle_{uuid4()}",
            provider_reference=provider_reference, observed_amount="26.00", observed_currency="USD",
        )
        assert result == "DISCREPANCY"
        assert conn.execute(
            "SELECT p.status FROM payments p JOIN provider_operations po ON po.payment_id=p.id WHERE po.id=%s",
            (operation_id,),
        ).fetchone()[0] == payment_status
        assert conn.execute(
            "SELECT discrepancy_code FROM reconciliation_records WHERE provider_operation_id=%s", (operation_id,)
        ).fetchone()[0] == "AMOUNT_MISMATCH"


def test_duplicate_settlement_report_is_noop():
    if not os.getenv("DATABASE_URL"):
        return
    with connection() as conn:
        with conn.transaction():
            _, provider_reference = _fixture(conn)
        settlement_reference = f"settle_{uuid4()}"
        repo = SettlementRepository(conn)
        assert repo.ingest(provider_name="mock", settlement_reference=settlement_reference,
                           provider_reference=provider_reference, observed_amount="25.00", observed_currency="USD") == "MATCHED"
        assert repo.ingest(provider_name="mock", settlement_reference=settlement_reference,
                           provider_reference=provider_reference, observed_amount="25.00", observed_currency="USD") == "DUPLICATE"
        assert conn.execute(
            "SELECT count(*) FROM settlements WHERE provider_name='mock' AND settlement_reference=%s",
            (settlement_reference,),
        ).fetchone()[0] == 1


def test_unknown_provider_reference_is_discrepancy():
    if not os.getenv("DATABASE_URL"):
        return
    with connection() as conn:
        result = SettlementRepository(conn).ingest(
            provider_name="mock", settlement_reference=f"settle_{uuid4()}",
            provider_reference=f"missing_{uuid4()}", observed_amount="10.00", observed_currency="USD",
        )
        assert result == "DISCREPANCY"
