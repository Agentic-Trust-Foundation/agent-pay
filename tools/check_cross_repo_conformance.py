"""Verify the pinned V1 ATF <-> Agent-Pay shared contract."""

import base64
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml


ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "conformance" / "v1" / "atf-agent-pay-contract-vectors.yaml"

ATF_REPOSITORY = "Agentic-Trust-Foundation/agentic-trust"
ATF_REF = "07f3e991ae0eb10ca4d838025f345467ab6684f3"
ATF_PATH = "conformance/v1/agent-pay-contract-vectors.yaml"
ATF_BLOB_SHA = "11b6939b65906aa0efc768d678b2356db383f7ec"


def load_local(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


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
            "User-Agent": "agent-pay-cross-repo-conformance",
        },
    )

    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise SystemExit(
            f"Unable to read pinned ATF conformance vector from GitHub "
            f"(HTTP {exc.code})."
        ) from exc
    except URLError as exc:
        raise SystemExit(
            f"Unable to reach GitHub while reading the pinned ATF "
            f"conformance vector: {exc.reason}"
        ) from exc

    if payload.get("encoding") != "base64" or "content" not in payload:
        raise SystemExit("GitHub did not return the expected ATF file content.")

    actual_blob_sha = payload.get("sha")
    if actual_blob_sha != ATF_BLOB_SHA:
        raise SystemExit(
            "ATF conformance vector blob mismatch: "
            f"expected {ATF_BLOB_SHA}, got {actual_blob_sha}"
        )

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

    digest = hashlib.sha256(
        LOCAL.read_bytes()
    ).hexdigest()
    print(
        "cross-repository conformance OK: "
        f"{len(local['vectors'])} vectors; "
        f"ATF ref={ATF_REF}; "
        f"ATF blob={ATF_BLOB_SHA}; "
        f"local sha256={digest}"
    )


if __name__ == "__main__":
    main()
