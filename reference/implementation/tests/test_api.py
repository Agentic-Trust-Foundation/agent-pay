from fastapi.testclient import TestClient

from agent_pay.api import app


client = TestClient(app)


def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_payment_requires_idempotency_key():
    response = client.post("/v1/payments", json={
        "agent_id": "00000000-0000-0000-0000-000000000001",
        "account_id": "00000000-0000-0000-0000-000000000002",
        "amount": {"value": "10.00", "currency": "USD"},
        "purpose": "test",
    })
    assert response.status_code == 400


def test_payment_requires_bearer_auth(monkeypatch):
    monkeypatch.setenv("AGENT_PAY_AUTH_MODE", "development")
    monkeypatch.setenv("AGENT_PAY_DEV_TOKEN", "ci-agent-token")
    monkeypatch.setenv("AGENT_PAY_DEV_AGENT_ID", "00000000-0000-0000-0000-000000000001")
    monkeypatch.setenv("AGENT_PAY_DEV_ACCOUNT_ID", "00000000-0000-0000-0000-000000000002")
    response = client.post(
        "/v1/payments",
        headers={"Idempotency-Key": "api-auth-test"},
        json={
            "agent_id": "00000000-0000-0000-0000-000000000001",
            "account_id": "00000000-0000-0000-0000-000000000002",
            "amount": {"value": "10.00", "currency": "USD"},
            "purpose": "test",
        },
    )
    assert response.status_code == 401
