"""Verify the V1 ATF <-> Agent-Pay shared contract."""

import base64
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml


ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "conformance" / "v1" / "atf-agent-pay-contract-vectors.yaml"

ATF_API_URL = (
    "https://api.github.com/repos/Agentic-Trust-Foundation/"
    "agentic-trust/contents/conformance/v1/agent-pay-contract-vectors.yaml"
)


def load_local(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_atf():
    request = Request(
        ATF_API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "agent-pay-cross-repo-conformance",
        },
    )

    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise SystemExit(
            f"Unable to read ATF conformance vector from GitHub "
            f"(HTTP {exc.code})."
        ) from exc
    except URLError as exc:
        raise SystemExit(
            f"Unable to reach GitHub while reading the ATF "
            f"conformance vector: {exc.reason}"
        ) from exc

    if payload.get("encoding") != "base64" or "content" not in payload:
        raise SystemExit("GitHub did not return the expected ATF file content.")

    content = base64.b64decode(payload["content"]).decode("utf-8")
    return yaml.safe_load(content)


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
    local = load_local(LOCAL)
    remote = load_atf()
    if normalized(local) != normalized(remote):
        raise SystemExit("ATF-Agent-Pay cross-repository vectors are inconsistent")
    print(f"cross-repository conformance OK: {len(local['vectors'])} vectors")


if __name__ == "__main__":
    main()
