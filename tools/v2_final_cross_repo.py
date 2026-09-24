import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATF_RAW = "https://raw.githubusercontent.com/Agentic-Trust-Foundation/agentic-trust/main/conformance/v2"

def load_local(phase):
    return json.loads((ROOT / "conformance/v2" / f"phase-{phase}" / "contract.json").read_text())

def load_atf(phase):
    with urllib.request.urlopen(f"{ATF_RAW}/phase-{phase}/contract.json", timeout=15) as r:
        return json.load(r)

def main():
    for phase in range(35, 43):
        local = load_local(phase)
        upstream = load_atf(phase)
        assert local["phase"] == phase
        assert local["protocol_version"] == "agent-pay/v2"
        assert local["upstream_protocol"] == "atf/v2"
        assert upstream["phase"] == phase
        assert upstream["protocol_version"] == "atf/v2"
        assert local["rules"] == upstream["rules"]
        assert [v["rule"] for v in local["vectors"]] == [v["rule"] for v in upstream["vectors"]]
        assert [v["expected_decision"] for v in local["vectors"]] == [v["expected_decision"] for v in upstream["vectors"]]
    print("Agent-Pay V2 final cross-repository verification: PASS")

if __name__ == "__main__":
    main()
