import json
import os
from decimal import Decimal
from uuid import uuid4

import pytest

from agent_pay.db import connection
from agent_pay.provider import ProviderOutcome
from agent_pay.provider_events import ProviderEventRepository
from agent_pay.settlement import SettlementRepository
from agent_pay.simulator import ProviderSimulator
from agent_pay.webhook_resolution import ProviderEventResolver

pytestmark = pytest.mark.integration


def test_postgres_timeout_webhook_settlement_e2e():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests")

    provider = ProviderSimulator()
    amount = Decimal("25.00")
    currency = "USD"
    with connection() as conn:
        with conn.transaction():
            account_id = conn.execute("INSERT INTO accounts (owner_reference) VALUES (%s) RETURNING id", (f"e2e-{uuid4()}",)).fetchone()[0]
            agent_id = conn.execute("INSERT INTO agents (account_id, name) VALUES (%s,%s) RETURNING id", (account_id, "e2e-agent")).fetchone()[0]
            wallet_id = conn.execute("INSERT INTO wallets (account_id, currency, balance, available_balance) VALUES (%s,%s,100,100) RETURNING id", (account_id, currency)).fetchone()[0]
            customer_ledger = conn.execute("INSERT INTO ledger_accounts (wallet_id, currency, account_type, name) VALUES (%s,%s,'CUSTOMER',%s) RETURNING id", (wallet_id, currency, f"e2e-customer-{uuid4()}")).fetchone()[0]
            clearing_ledger = conn.execute("INSERT INTO ledger_accounts (currency, account_type, name) VALUES (%s,'CLEARING',%s) RETURNING id", (currency, f"e2e-clearing-{uuid4()}")).fetchone()[0]
            conn.execute("INSERT INTO payment_provider_accounts (provider_name, currency, ledger_account_id) VALUES ('mock',%s,%s)", (currency, clearing_ledger))
            policy_id = conn.execute("INSERT INTO policies (account_id, name, rules) VALUES (%s,%s,%s::jsonb) RETURNING id", (account_id, f"e2e-policy-{uuid4()}", '{"limits":{"per_transaction":100}}')).fetchone()[0]
            policy_version = conn.execute("INSERT INTO policy_versions (policy_id, version, rules) VALUES (%s,1,%s::jsonb) RETURNING id", (policy_id, '{"limits":{"per_transaction":100}}')).fetchone()[0]
            budget_id = conn.execute("INSERT INTO budgets (account_id, policy_id, name, currency, limit_amount) VALUES (%s,%s,%s,%s,100) RETURNING id", (account_id, policy_id, f"e2e-budget-{uuid4()}", currency)).fetchone()[0]
            request_id = conn.execute("INSERT INTO payment_requests (account_id, agent_id, amount, currency, purpose, idempotency_key, policy_version_id, budget_id) VALUES (%s,%s,%s,%s,'e2e purchase',%s,%s,%s) RETURNING id", (account_id, agent_id, amount, currency, f"e2e:{uuid4()}", policy_version, budget_id)).fetchone()[0]
            payment_id = conn.execute("INSERT INTO payments (payment_request_id, amount, currency, status) VALUES (%s,%s,%s,'UNKNOWN_EXTERNAL_OUTCOME') RETURNING id", (request_id, amount, currency)).fetchone()[0]
            reservation_id = conn.execute("INSERT INTO budget_reservations (budget_id, payment_request_id, amount, currency) VALUES (%s,%s,%s,%s) RETURNING id", (budget_id, request_id, amount, currency)).fetchone()[0]
            conn.execute("UPDATE budgets SET reserved_amount=%s WHERE id=%s", (amount, budget_id))
            conn.execute("UPDATE payment_requests SET budget_reservation_id=%s WHERE id=%s", (reservation_id, request_id))
            operation_id = conn.execute("INSERT INTO provider_operations (payment_id, operation_type, idempotency_key, status) VALUES (%s,'CHARGE',%s,'PENDING') RETURNING id", (payment_id, f"payment:{payment_id}:charge")).fetchone()[0]

        assert provider.charge(str(payment_id), amount, currency, outcome=ProviderOutcome.UNKNOWN) == ProviderOutcome.UNKNOWN
        body, _ = provider.webhook(str(payment_id))
        payload = json.loads(body)
        event_id = ProviderEventRepository(conn).record(provider_name="mock", event_id=payload["event_id"], event_type=payload["event_type"], payload=payload, signature_valid=True)
        conn.execute("UPDATE provider_events SET provider_operation_id=%s WHERE id=%s", (operation_id, event_id))
        assert ProviderEventResolver(conn).resolve(event_id=event_id, provider_operation_id=operation_id, outcome="SUCCEEDED", provider_reference=payload["provider_reference"], customer_ledger_account_id=customer_ledger, clearing_ledger_account_id=clearing_ledger, correlation_id="e2e") == "RESOLVED"
        assert conn.execute("SELECT status, provider_reference FROM payments WHERE id=%s", (payment_id,)).fetchone() == ("SUCCEEDED", payload["provider_reference"])
        assert conn.execute("SELECT status FROM budget_reservations WHERE id=%s", (reservation_id,)).fetchone()[0] == "CONSUMED"
        assert conn.execute("SELECT count(*) FROM ledger_journals WHERE reference_id=%s", (payment_id,)).fetchone()[0] == 1

        assert ProviderEventResolver(conn).resolve(event_id=event_id, provider_operation_id=operation_id, outcome="SUCCEEDED", provider_reference=payload["provider_reference"], customer_ledger_account_id=customer_ledger, clearing_ledger_account_id=clearing_ledger, correlation_id="e2e-replay") == "DUPLICATE"
        assert conn.execute("SELECT count(*) FROM ledger_journals WHERE reference_id=%s", (payment_id,)).fetchone()[0] == 1
        assert conn.execute("SELECT status FROM budget_reservations WHERE id=%s", (reservation_id,)).fetchone()[0] == "CONSUMED"
        assert ProviderEventRepository(conn).record(provider_name="mock", event_id=payload["event_id"], event_type=payload["event_type"], payload=payload, signature_valid=True) is None

        settlement = provider.settlement(str(payment_id))
        assert SettlementRepository(conn).ingest(provider_name="mock", settlement_reference=settlement["settlement_reference"], provider_reference=settlement["provider_reference"], observed_amount=settlement["amount"], observed_currency=settlement["currency"]) == "MATCHED"
        assert SettlementRepository(conn).ingest(provider_name="mock", settlement_reference=settlement["settlement_reference"], provider_reference=settlement["provider_reference"], observed_amount=settlement["amount"], observed_currency=settlement["currency"]) == "DUPLICATE"

        mismatch_reference = f"set_mismatch_{uuid4()}"
        assert SettlementRepository(conn).ingest(provider_name="mock", settlement_reference=mismatch_reference, provider_reference=settlement["provider_reference"], observed_amount="24.00", observed_currency=currency) == "DISCREPANCY"
        assert conn.execute("SELECT rr.status, rr.discrepancy_code FROM reconciliation_records rr JOIN settlements s ON s.id=rr.settlement_id WHERE s.settlement_reference=%s", (mismatch_reference,)).fetchone() == ("DISCREPANCY", "AMOUNT_MISMATCH")

        currency_reference = f"set_currency_{uuid4()}"
        assert SettlementRepository(conn).ingest(provider_name="mock", settlement_reference=currency_reference, provider_reference=settlement["provider_reference"], observed_amount=settlement["amount"], observed_currency="EUR") == "DISCREPANCY"
        assert conn.execute("SELECT rr.status, rr.discrepancy_code FROM reconciliation_records rr JOIN settlements s ON s.id=rr.settlement_id WHERE s.settlement_reference=%s", (currency_reference,)).fetchone() == ("DISCREPANCY", "CURRENCY_MISMATCH")

        unknown_reference = f"set_unknown_{uuid4()}"
        assert SettlementRepository(conn).ingest(provider_name="mock", settlement_reference=unknown_reference, provider_reference="provider-ref-does-not-exist", observed_amount=amount, observed_currency=currency) == "DISCREPANCY"
        assert conn.execute("SELECT rr.status, rr.discrepancy_code FROM reconciliation_records rr JOIN settlements s ON s.id=rr.settlement_id WHERE s.settlement_reference=%s", (unknown_reference,)).fetchone() == ("DISCREPANCY", "UNKNOWN_PROVIDER_REFERENCE")
        assert conn.execute("SELECT count(*) FROM ledger_journals WHERE reference_id=%s", (payment_id,)).fetchone()[0] == 1
