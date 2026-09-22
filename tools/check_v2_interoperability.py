"""Independently verify the Phase 25 ATF <-> Agent-Pay V2 vector contract."""

import base64
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "conformance" / "v2" / "interoperability-vectors.yaml"

ATF_REPOSITORY = "Agentic-Trust-Foundation/agentic-trust"
ATF_REF = "ae3338e69127cdacdcadb5ac7a9a4c97fee2fbdf"
ATF_PATH = "conformance/v2/interoperability-vectors.yaml"
ATF_BLOB_SHA = "4a0fd304389f4df124a359d1de9c3f3253050b36"


def load_atf():
    url = (
        f"https://api.github.com/repos/{ATF_REPOSITORY}/contents/"
        f"{ATF_PATH}?ref={ATF_REF}"
    )
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "agent-pay-v2-interoperability-conformance",
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise SystemExit(f"Unable to read pinned ATF V2 vectors (HTTP {exc.code}).") from exc
    except URLError as exc:
        raise SystemExit(f"Unable to reach GitHub: {exc.reason}") from exc

    if payload.get("encoding") != "base64" or "content" not in payload:
        raise SystemExit("GitHub did not return the expected ATF V2 vector content.")
    if payload.get("sha") != ATF_BLOB_SHA:
        raise SystemExit(
            f"ATF V2 vector blob mismatch: expected {ATF_BLOB_SHA}, got {payload.get('sha')}"
        )
    return yaml.safe_load(base64.b64decode(payload["content"]).decode("utf-8"))


def normalized(document):
    return {
        "phase": document["phase"],
        "vectors": [
            {"id": item["id"], "expected": item["expected"]}
            for item in document["vectors"]
        ],
    }


def main():
    local = yaml.safe_load(LOCAL.read_text(encoding="utf-8"))
    remote = load_atf()

    if local.get("version") != "agent-pay/v2":
        raise SystemExit("unexpected Agent-Pay V2 interoperability version")
    if normalized(local) != normalized(remote):
        raise SystemExit("ATF and Agent-Pay V2 interoperability vectors are inconsistent")

    digest = hashlib.sha256(LOCAL.read_bytes()).hexdigest()
    print(
        "Agent-Pay V2 interoperability contract OK: "
        f"{len(local['vectors'])} vectors; "
        f"implementation=agent-pay-reference-validator/1; "
        f"ATF ref={ATF_REF}; ATF blob={ATF_BLOB_SHA}; local sha256={digest}"
    )


if __name__ == "__main__":
    main()
