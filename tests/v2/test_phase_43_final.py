import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "conformance/v2/phase-43/contract.json"
VECTORS = ROOT / "conformance/v2/phase-43/vectors.json"

def test_phase_43_contract():
    c = json.loads(CONTRACT.read_text())
    assert c["phase"] == 43
    assert c["protocol_version"] == "agent-pay/v2"
    assert c["upstream_protocol"] == "atf/v2"
    assert len(c["vectors"]) == 6
    assert c["vectors"][-1]["expected_decision"] == "DENY"
    assert c["vectors"][-1]["rule"] == "fail-closed"

def test_phase_43_vectors():
    c = json.loads(CONTRACT.read_text())
    v = json.loads(VECTORS.read_text())
    assert c["vectors"] == [{"id": x["case_id"], "expected_decision": x["expected_decision"], "rule": x["rule"]} for x in v]
