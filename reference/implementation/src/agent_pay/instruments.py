from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class InstrumentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class InstrumentType(StrEnum):
    WALLET = "WALLET"
    VIRTUAL_CARD = "VIRTUAL_CARD"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    PAYMENT_GATEWAY = "PAYMENT_GATEWAY"
    OTHER = "OTHER"


class InstrumentEligibilityError(ValueError):
    """Raised when a payment instrument cannot be used for an intent."""


@dataclass(frozen=True)
class PaymentInstrument:
    """Credential-free representation of an Agent-Pay payment instrument."""

    instrument_id: str
    account_id: str
    instrument_type: InstrumentType
    currency: str
    status: InstrumentStatus = InstrumentStatus.ACTIVE
    merchant_domains: frozenset[str] = frozenset()
    provider_reference: str | None = None

    def validate(self, *, account_id: str, currency: str, merchant_domain: str | None = None) -> None:
        if self.account_id != account_id:
            raise InstrumentEligibilityError("payment instrument belongs to a different account")
        if self.status is not InstrumentStatus.ACTIVE:
            raise InstrumentEligibilityError(f"payment instrument is {self.status.value.lower()}")
        if self.currency.upper() != currency.upper():
            raise InstrumentEligibilityError("payment instrument currency is incompatible")
        if self.merchant_domains and merchant_domain not in self.merchant_domains:
            raise InstrumentEligibilityError("payment instrument is not permitted for this merchant")


class InstrumentSelector:
    """Deterministic, side-effect-free selection of an eligible instrument."""

    def __init__(self, instruments: list[PaymentInstrument]) -> None:
        self._instruments = tuple(instruments)

    def select(self, *, account_id: str, currency: str, merchant_domain: str | None = None) -> PaymentInstrument:
        errors: list[str] = []
        for instrument in self._instruments:
            try:
                instrument.validate(
                    account_id=account_id,
                    currency=currency,
                    merchant_domain=merchant_domain,
                )
            except InstrumentEligibilityError as exc:
                errors.append(f"{instrument.instrument_id}: {exc}")
                continue
            return instrument
        detail = "; ".join(errors) if errors else "no instruments configured"
        raise InstrumentEligibilityError(f"no eligible payment instrument: {detail}")
