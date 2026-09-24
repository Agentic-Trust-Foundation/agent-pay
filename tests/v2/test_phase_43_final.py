import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "conformance/v2/phase-43/contract.json"
VECTORS = ROOT / "conformance/v2/phase-43/vectors.json"

class Phase43FinalTests(unittest.TestCase):
    def test_phase_43_contract(self):
        c = json.loads(CONTRACT.read_text())
        self.assertEqual(c["phase"], 43)
        self.assertEqual(c["protocol_version"], "agent-pay/v2")
        self.assertEqual(c["upstream_protocol"], "atf/v2")
        self.assertEqual(len(c["vectors"]), 6)
        self.assertEqual(c["vectors"][-1]["expected_decision"], "DENY")
        self.assertEqual(c["vectors"][-1]["rule"], "fail-closed")

    def test_phase_43_vectors(self):
        c = json.loads(CONTRACT.read_text())
        v = json.loads(VECTORS.read_text())
        self.assertEqual(
            c["vectors"],
            [{"id": x["case_id"], "expected_decision": x["expected_decision"], "rule": x["rule"]} for x in v],
        )

if __name__ == "__main__":
    unittest.main()
