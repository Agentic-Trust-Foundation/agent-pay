from fastapi.routing import APIRoute

from agent_pay.api import app


def _routes() -> set[tuple[str, str]]:
    return {
        (method, route.path)
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in route.methods
    }


def test_v1_financial_http_surface_is_mounted():
    routes = _routes()
    required = {
        ("POST", "/v1/payments"),
        ("GET", "/v1/payments/{payment_id}"),
        ("POST", "/v1/payments/{payment_id}/capture"),
        ("POST", "/v1/payments/{payment_id}/void"),
        ("POST", "/v1/payments/{payment_id}/refund"),
        ("POST", "/v1/providers/{provider_name}/webhooks"),
        ("POST", "/v1/providers/{provider_name}/settlements"),
    }
    assert required <= routes
