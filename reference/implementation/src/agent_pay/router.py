from __future__ import annotations

from dataclasses import dataclass

from .provider import PaymentProvider


class ProviderRoutingError(ValueError):
    """Raised when no payment provider can serve a payment intent."""


@dataclass(frozen=True)
class ProviderRoute:
    provider_id: str
    provider: PaymentProvider
    merchant_domains: frozenset[str] = frozenset()
    currencies: frozenset[str] = frozenset()

    def matches(self, merchant_domain: str, currency: str) -> bool:
        domain_ok = not self.merchant_domains or merchant_domain in self.merchant_domains
        currency_ok = not self.currencies or currency in self.currencies
        return domain_ok and currency_ok


class PaymentRouter(PaymentProvider):
    """Deterministic provider router with explicit routes and a safe default."""

    def __init__(self) -> None:
        self._routes: list[ProviderRoute] = []
        self._by_id: dict[str, ProviderRoute] = {}

    def register(
        self,
        provider_id: str,
        provider: PaymentProvider,
        *,
        merchant_domains: set[str] | frozenset[str] | None = None,
        currencies: set[str] | frozenset[str] | None = None,
    ) -> None:
        if provider_id in self._by_id:
            raise ValueError(f"provider already registered: {provider_id}")
        route = ProviderRoute(
            provider_id=provider_id,
            provider=provider,
            merchant_domains=frozenset(merchant_domains or ()),
            currencies=frozenset(currencies or ()),
        )
        self._routes.append(route)
        self._by_id[provider_id] = route

    def for_payment(self, merchant_domain: str, currency: str) -> PaymentProvider:
        for route in self._routes:
            if route.matches(merchant_domain, currency):
                return route.provider
        raise ProviderRoutingError(
            f"no payment provider route for domain={merchant_domain!r}, currency={currency!r}"
        )

    def provider_id_for(self, merchant_domain: str, currency: str) -> str:
        for route in self._routes:
            if route.matches(merchant_domain, currency):
                return route.provider_id
        raise ProviderRoutingError(
            f"no payment provider route for domain={merchant_domain!r}, currency={currency!r}"
        )

    def _provider(self, payment_id: str) -> PaymentProvider:
        if not self._routes:
            raise ProviderRoutingError("no payment providers registered")
        # Direct PaymentProvider compatibility path; PaymentService uses for_payment().
        return self._routes[0].provider

    def charge(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str):
        return self._provider(payment_id).charge(payment_id, amount_minor, currency, idempotency_key)

    def capture(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str):
        return self._provider(payment_id).capture(payment_id, amount_minor, currency, idempotency_key)

    def void(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str):
        return self._provider(payment_id).void(payment_id, amount_minor, currency, idempotency_key)

    def refund(self, payment_id: str, amount_minor: int, currency: str, idempotency_key: str):
        return self._provider(payment_id).refund(payment_id, amount_minor, currency, idempotency_key)
