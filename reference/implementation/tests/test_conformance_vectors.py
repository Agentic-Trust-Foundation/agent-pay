from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
VECTORS = ROOT / "conformance" / "v1" / "payment-control-vectors.yaml"


def test_v1_vectors_are_machine_readable_and_complete():
    document = yaml.safe_load(VECTORS.read_text(encoding="utf-8"))
    assert document["version"] == 1
    assert document["suite"] == "agent-pay-financial-control-v1"
    vectors = document["vectors"]
    assert len(vectors) >= 16
    ids = [item["id"] for item in vectors]
    assert len(ids) == len(set(ids))
    for vector in vectors:
        assert vector["id"]
        assert vector["invariant"]
        assert vector.get("given") or vector.get("when")
        assert vector["expect"]
