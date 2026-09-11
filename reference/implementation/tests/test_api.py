from fastapi.testclient import TestClient

from agent_pay.api import CreatePayment, app, request_fingerprint


client = TestClient(app)


def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_payment_requires_idempotency_key():
    response = client.post("/v1/payments", json={
        "agent_id": "00000000-0000-0000-0000-000000000001",
        "account_id": "00000000-0000-0000-0000-000000000002",
        "amount": {"value": "10.00", "currency": "USD"}, "purpose": "test",
    })
    assert response.status_code == 400


def test_payment_requires_bearer_auth(monkeypatch):
    monkeypatch.setenv("AGENT_PAY_AUTH_MODE", "development")
    monkeypatch.setenv("AGENT_PAY_DEV_TOKEN", "ci-agent-token")
    monkeypatch.setenv("AGENT_PAY_DEV_AGENT_ID", "00000000-0000-0000-0000-000000000001")
    monkeypatch.setenv("AGENT_PAY_DEV_ACCOUNT_ID", "00000000-0000-0000-0000-000000000002")
    response = client.post("/v1/payments", headers={"Idempotency-Key": "api-auth-test"}, json={
        "agent_id": "00000000-0000-0000-0000-000000000001",
        "account_id": "00000000-0000-0000-0000-000000000002",
        "amount": {"value": "10.00", "currency": "USD"}, "purpose": "test",
    })
    assert response.status_code == 401


def test_approval_requires_separate_human_auth():
    response = client.post("/v1/approvals/00000000-0000-0000-0000-000000000003/approve")
    assert response.status_code == 401


def test_request_fingerprint_is_stable():
    request = CreatePayment.model_validate({
        "agent_id": "00000000-0000-0000-0000-000000000001",
        "account_id": "00000000-0000-0000-0000-000000000002",
        "amount": {"value": "10.00", "currency": "USD"}, "purpose": "test",
    })
    assert request_fingerprint(request) == request_fingerprint(request)


def test_request_fingerprint_changes_on_material_intent_change():
    base = CreatePayment.model_validate({
        "agent_id": "00000000-0000-0000-0000-000000000001",
        "account_id": "00000000-0000-0000-0000-000000000002",
        "amount": {"value": "10.00", "currency": "USD"}, "purpose": "test",
    })
    changed = base.model_copy(update={"purpose": "different"})
    assert request_fingerprint(base) != request_fingerprint(changed)


def test_request_fingerprint_includes_control_selection():
    base = CreatePayment.model_validate({
        "agent_id": "00000000-0000-0000-0000-000000000001",
        "account_id": "00000000-0000-0000-0000-000000000002",
        "amount": {"value": "10.00", "currency": "USD"}, "purpose": "test",
    })
    changed = base.model_copy(update={"budget_id": "00000000-0000-0000-0000-000000000003"})
    assert request_fingerprint(base) != request_fingerprint(changed)
