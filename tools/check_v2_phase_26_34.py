#!/usr/bin/env python3
import hashlib, urllib.request, yaml
ATF_SHA="382ee3a422b67f7c337a3cef48eb981e3a265dbd"
url=f"https://raw.githubusercontent.com/Agentic-Trust-Foundation/agentic-trust/{ATF_SHA}/conformance/v2/phase-26-34-vectors.yaml"
with urllib.request.urlopen(url) as r: upstream=r.read()
local=open("conformance/v2/phase-26-34-vectors.yaml","rb").read()
a=yaml.safe_load(upstream); b=yaml.safe_load(local)
assert a["phase"]==b["phase"]==26
assert {v["id"]:v["expected_decision"] for v in a["vectors"]}=={v["id"]:v["expected_decision"] for v in b["vectors"]}
assert len(a["vectors"])==20
print("implementation=agent-pay-v2-contract-validator/1")
print("upstream_atf_commit="+ATF_SHA)
print("upstream_vector_sha256="+hashlib.sha256(upstream).hexdigest())
print("vectors=20")
