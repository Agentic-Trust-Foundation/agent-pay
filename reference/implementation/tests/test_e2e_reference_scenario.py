from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
SCENARIO = ROOT / "examples" / "v1" / "end-to-end-agent-payment.yaml"


def test_reference_scenario_contains_complete_v1_boundary_trace():
    document = yaml.safe_load(SCENARIO.read_text(encoding="utf-8"))

    assert document["version"] == 1
    assert document["authority"]["source"] == "agentic-trust"
    assert document["authority"]["scope"] == ["PAYMENT"]
    assert document["authority"]["max_amount"] == "100.00"
    assert document["payment_request"]["amount"] == "75.00"
    assert document["policy"]["result"] == "APPROVAL_REQUIRED"
    assert document["approval"]["status"] == "APPROVED"
    assert document["budget"]["reservation_status"] == "RESERVED"
    assert document["provider"]["outcome"] == "SUCCEEDED"
    assert document["financial_effect"]["ledger"]["balanced"] is True
    assert document["settlement"]["result"] == "MATCHED"
    assert document["terminal_state"]["payment"] == "SUCCEEDED"
    assert document["terminal_state"]["external_settlement"] == "RECONCILED"
