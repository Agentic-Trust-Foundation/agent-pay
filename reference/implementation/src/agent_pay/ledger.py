from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from uuid import UUID


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


def post_journal(conn, *, currency: str, reference_type: str, reference_id: UUID | None,
                 idempotency_key: str, correlation_id: str | None,
                 postings: list[dict]) -> UUID:
    """Persist a balanced double-entry journal inside the caller's transaction."""
    amounts = [Decimal(str(p["amount"])) for p in postings]
    debit = sum((a for p, a in zip(postings, amounts) if p["side"] == "DEBIT"), Decimal("0"))
    credit = sum((a for p, a in zip(postings, amounts) if p["side"] == "CREDIT"), Decimal("0"))
    if not postings or debit <= 0 or credit <= 0 or debit != credit:
        raise ValueError("ledger journal must be balanced")
    if any(p["currency"] != currency for p in postings):
        raise ValueError("all postings must use the journal currency")

    inserted = conn.execute(
        """INSERT INTO ledger_journals
           (currency, reference_type, reference_id, idempotency_key, correlation_id)
           VALUES (%s, %s, %s, %s, %s)
           ON CONFLICT (idempotency_key) DO NOTHING
           RETURNING id""",
        (currency, reference_type, reference_id, idempotency_key, correlation_id),
    ).fetchone()

    if inserted:
        journal_id = inserted[0]
        for p in postings:
            conn.execute(
                """INSERT INTO ledger_postings
                   (journal_id, ledger_account_id, side, amount, currency)
                   VALUES (%s, %s, %s, %s, %s)""",
                (journal_id, p["ledger_account_id"], p["side"], p["amount"], p["currency"]),
            )
        return journal_id

    existing = conn.execute(
        """SELECT id, currency, reference_type, reference_id, correlation_id
           FROM ledger_journals
           WHERE idempotency_key=%s
           FOR UPDATE""",
        (idempotency_key,),
    ).fetchone()
    if not existing:
        raise RuntimeError("ledger journal conflict could not be resolved")

    journal_id, existing_currency, existing_reference_type, existing_reference_id, existing_correlation_id = existing
    existing_postings = conn.execute(
        """SELECT ledger_account_id, side, amount, currency
           FROM ledger_postings
           WHERE journal_id=%s
           ORDER BY id""",
        (journal_id,),
    ).fetchall()
    requested_postings = [
        (str(p["ledger_account_id"]), p["side"], Decimal(str(p["amount"])), p["currency"])
        for p in postings
    ]
    stored_postings = [
        (str(account_id), side, Decimal(str(amount)), posting_currency)
        for account_id, side, amount, posting_currency in existing_postings
    ]

    if (
        existing_currency != currency
        or existing_reference_type != reference_type
        or existing_reference_id != reference_id
        or existing_correlation_id != correlation_id
        or stored_postings != requested_postings
    ):
        raise ValueError("ledger idempotency key conflict")
    return journal_id
