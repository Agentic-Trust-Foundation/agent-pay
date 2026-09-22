#!/usr/bin/env python3
import hashlib
import urllib.request

import yaml

ATF_COMMIT = "e30fb82044ef3a67da38e77ebdf82c437d313b39"
EXPECTED_UPSTREAM_SHA256 = "ede4631f3153894a319cdd1bbc7b9ff2d7ed29b77c179cfcad3cd91e4c86ee86"
URL = (
    f"https://raw.githubusercontent.com/Agentic-Trust-Foundation/agentic-trust/"
    f"{ATF_COMMIT}/conformance/v2/phase-26-34-vectors.yaml"
)

with urllib.request.urlopen(URL) as response:
    upstream = response.read()

actual_sha256 = hashlib.sha256(upstream).hexdigest()
assert actual_sha256 == EXPECTED_UPSTREAM_SHA256, "upstream vector digest mismatch"

local = open("conformance/v2/phase-26-34-vectors.yaml", "rb").read()
a = yaml.safe_load(upstream)
b = yaml.safe_load(local)

assert a["phase"] == b["phase"] == 26
assert a["protocol_version"] == "atf/v2"
assert b["protocol_version"] == "agent-pay/v2"
assert {v["id"]: v["expected_decision"] for v in a["vectors"]} == {
    v["id"]: v["expected_decision"] for v in b["vectors"]
}
assert len(a["vectors"]) == len(b["vectors"]) == 20

print("implementation=agent-pay-v2-contract-validator/1")
print("upstream_atf_commit=" + ATF_COMMIT)
print("upstream_vector_sha256=" + actual_sha256)
print("vectors=20")
