from fastapi.testclient import TestClient
from agent_pay.api import app


def test_healthz():
    response = TestClient(app).get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_payment_requires_idempotency_key():
    response = TestClient(app).post("/v1/payments", json={
        "agent_id": "00000000-0000-0000-0000-000000000001",
        "account_id": "00000000-0000-0000-0000-000000000002",
        "amount": {"value": "10.00", "currency": "USD"},
        "purpose": "test",
    })
    assert response.status_code == 400
