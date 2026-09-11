from dataclasses import dataclass
from decimal import Decimal
from threading import Lock


@dataclass
class Budget:
    limit: Decimal
    consumed: Decimal = Decimal("0")
    reserved: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        self._lock = Lock()

    @property
    def available(self) -> Decimal:
        return self.limit - self.consumed - self.reserved

    def reserve(self, amount: Decimal) -> bool:
        if amount <= 0:
            raise ValueError("reservation amount must be positive")
        with self._lock:
            if amount > self.available:
                return False
            self.reserved += amount
            return True

    def release(self, amount: Decimal) -> None:
        with self._lock:
            if amount > self.reserved:
                raise ValueError("cannot release more than reserved")
            self.reserved -= amount

    def consume(self, amount: Decimal) -> None:
        with self._lock:
            if amount > self.reserved:
                raise ValueError("cannot consume more than reserved")
            self.reserved -= amount
            self.consumed += amount
