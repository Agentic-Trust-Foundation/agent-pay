"""Verify the V1 ATF <-> Agent-Pay shared contract."""
from pathlib import Path
from urllib.request import urlopen

import yaml


ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "conformance" / "v1" / "atf-agent-pay-contract-vectors.yaml"
ATF_URL = (
    "https://raw.githubusercontent.com/"
    "Agentic-Trust-Foundation/agentic-trust/main/"
    "conformance/v1/agent-pay-contract-vectors.yaml"
)


def load_yaml(path_or_url: str):
    if path_or_url.startswith("http"):
        with urlopen(path_or_url, timeout=15) as response:
            return yaml.safe_load(response.read().decode("utf-8"))
    return yaml.safe_load(Path(path_or_url).read_text(encoding="utf-8"))


def normalized(document):
    return {
        "version": document["version"],
        "suite": document["suite"],
        "vectors": [
            {
                "id": item["id"],
                "invariant": item["invariant"],
                "expect": item["expect"],
            }
            for item in document["vectors"]
        ],
    }


def main():
    local = load_yaml(str(LOCAL))
    remote = load_yaml(ATF_URL)
    if normalized(local) != normalized(remote):
        raise SystemExit("ATF-Agent-Pay cross-repository vectors are inconsistent")
    print(f"cross-repository conformance OK: {len(local['vectors'])} vectors")


if __name__ == "__main__":
    main()
