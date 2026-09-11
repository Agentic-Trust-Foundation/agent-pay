from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class Direction(StrEnum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


@dataclass(frozen=True)
class Posting:
    account_id: str
    direction: Direction
    amount: Decimal
    currency: str


@dataclass(frozen=True)
class Journal:
    journal_id: str
    postings: tuple[Posting, ...]

    def validate(self) -> None:
        if not self.postings:
            raise ValueError("journal must contain postings")
        currencies = {p.currency for p in self.postings}
        if len(currencies) != 1:
            raise ValueError("journal must contain one currency")
        debit = sum((p.amount for p in self.postings if p.direction == Direction.DEBIT), Decimal("0"))
        credit = sum((p.amount for p in self.postings if p.direction == Direction.CREDIT), Decimal("0"))
        if debit <= 0 or credit <= 0 or debit != credit:
            raise ValueError("journal is not balanced")
        if any(p.amount <= 0 for p in self.postings):
            raise ValueError("posting amount must be positive")


class InMemoryLedger:
    def __init__(self) -> None:
        self.journals: dict[str, Journal] = {}

    def post(self, journal: Journal) -> None:
        journal.validate()
        if journal.journal_id in self.journals:
            if self.journals[journal.journal_id] != journal:
                raise ValueError("journal id conflict")
            return
        self.journals[journal.journal_id] = journal
