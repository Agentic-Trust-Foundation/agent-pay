from decimal import Decimal

import pytest

from agent_pay.ledger import Direction, InMemoryLedger, Journal, Posting
from agent_pay.outbox import InMemoryOutbox, new_event


def balanced_journal():
    return Journal(
        "j1",
        (
            Posting("cash", Direction.DEBIT, Decimal("100"), "USD"),
            Posting("merchant", Direction.CREDIT, Decimal("100"), "USD"),
        ),
    )


def test_double_entry_journal_must_balance():
    ledger = InMemoryLedger()
    ledger.post(balanced_journal())
    ledger.post(balanced_journal())
    assert len(ledger.journals) == 1


def test_unbalanced_journal_is_rejected():
    with pytest.raises(ValueError, match="not balanced"):
        Journal(
            "j2",
            (
                Posting("cash", Direction.DEBIT, Decimal("100"), "USD"),
                Posting("merchant", Direction.CREDIT, Decimal("99"), "USD"),
            ),
        ).validate()


def test_outbox_is_idempotent_by_event_id():
    outbox = InMemoryOutbox()
    event = new_event("evt-1", "PaymentSucceeded", "pay-1", {"amount": "100"})
    outbox.append(event)
    outbox.append(event)
    assert len(outbox.pending()) == 1


def test_outbox_event_id_conflict_is_rejected():
    outbox = InMemoryOutbox()
    outbox.append(new_event("evt-1", "PaymentSucceeded", "pay-1", {}))
    with pytest.raises(ValueError, match="outbox event id conflict"):
        outbox.append(new_event("evt-1", "PaymentFailed", "pay-1", {}))
