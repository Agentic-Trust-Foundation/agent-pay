"""Small provider-neutral observability primitives for the reference implementation.

Financial state remains in PostgreSQL; these helpers only produce measurements
and structured correlation metadata. They are intentionally dependency-free so
an operator can connect them to Prometheus, OpenTelemetry, or another backend.
"""
from dataclasses import dataclass, field
from time import monotonic


@dataclass
class Counter:
    name: str
    value: int = 0
    labels: dict[tuple[tuple[str, str], ...], int] = field(default_factory=dict)

    def inc(self, amount: int = 1, **labels: str) -> None:
        key = tuple(sorted((str(k), str(v)) for k, v in labels.items()))
        self.labels[key] = self.labels.get(key, 0) + amount
        self.value += amount


@dataclass
class Timer:
    name: str

    def measure(self):
        return _TimerContext(self)


class _TimerContext:
    def __init__(self, timer: Timer):
        self.timer = timer
        self.elapsed_seconds: float | None = None

    def __enter__(self):
        self._started = monotonic()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.elapsed_seconds = monotonic() - self._started
        return False


payment_requests_total = Counter("agent_pay_payment_requests_total")
payment_outcomes_total = Counter("agent_pay_payment_outcomes_total")
provider_events_total = Counter("agent_pay_provider_events_total")
reconciliation_discrepancies_total = Counter("agent_pay_reconciliation_discrepancies_total")
payment_processing_time = Timer("agent_pay_payment_processing_seconds")
