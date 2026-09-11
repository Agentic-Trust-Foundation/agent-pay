from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[3]
OPENAPI = ROOT / "specs" / "v1" / "openapi.yaml"


@pytest.mark.conformance
def test_openapi_v1_declares_implemented_financial_surface():
    document = yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))
    assert document["openapi"] == "3.0.3"
    paths = document["paths"]
    for path in (
        "/payments",
        "/payments/{paymentId}",
        "/payments/{paymentId}/capture",
        "/payments/{paymentId}/void",
        "/payments/{paymentId}/refund",
        "/providers/{providerName}/webhooks",
        "/providers/{providerName}/settlements",
    ):
        assert path in paths
    assert paths["/payments"]["post"]["responses"]["202"]
    assert "ProblemDetails" in document["components"]["schemas"]
