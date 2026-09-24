import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    for phase in range(35, 44):
        p = ROOT / "conformance" / "v2" / f"phase-{phase}" / "contract.json"
        c = json.loads(p.read_text())
        assert c["phase"] == phase, (phase, c["phase"])
        assert c["protocol_version"] == "agent-pay/v2"
        assert c.get("upstream_protocol") == "atf/v2"
        rules = c["rules"]
        assert len(c["vectors"]) == len(rules) + 1
        assert c["vectors"][-1]["expected_decision"] == "DENY"
        assert c["vectors"][-1]["rule"] == "fail-closed"
        for v in c["vectors"][:-1]:
            assert v["expected_decision"] in {"ALLOW","DENY","REQUIRE_HUMAN"}
            assert v["rule"] in rules
    print("Agent-Pay V2 phases 35-43: PASS")

if __name__ == "__main__":
    main()
