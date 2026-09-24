#!/usr/bin/env python3
import json, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE="https://raw.githubusercontent.com/Agentic-Trust-Foundation/agentic-trust/main/conformance/v2"
for p in range(35,43):
    local=json.loads((ROOT/f"conformance/v2/phase-{p}/contract.json").read_text())
    with urllib.request.urlopen(f"{BASE}/phase-{p}/contract.json",timeout=20) as r:
        upstream=json.load(r)
    assert local["phase"]==p and upstream["phase"]==p
    assert local["upstream_protocol"]=="atf/v2"
    assert local["rules"]==upstream["rules"], p
    assert len(local["vectors"])==len(upstream["vectors"]), p
    for v in local["vectors"]:
        assert v["rule"]=="fail-closed" or v["rule"] in local["rules"]
print("Agent-Pay V2 phases 35-42: PASS; ATF cross-repository parity: PASS")
