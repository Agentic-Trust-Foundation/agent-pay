from decimal import Decimal
from agent_pay.ledger import Direction, InMemoryLedger, Journal, Posting


def test_balanced_journal_is_accepted():
    ledger = InMemoryLedger()
    ledger.post(Journal("j1", (
        Posting("cash", Direction.DEBIT, Decimal("10.00"), "USD"),
        Posting("merchant", Direction.CREDIT, Decimal("10.00"), "USD"),
    )))
    assert "j1" in ledger.journals


def test_unbalanced_journal_is_rejected():
    ledger = InMemoryLedger()
    journal = Journal("j2", (
        Posting("cash", Direction.DEBIT, Decimal("10.00"), "USD"),
        Posting("merchant", Direction.CREDIT, Decimal("9.00"), "USD"),
    ))
    try:
        ledger.post(journal)
        assert False, "expected ValueError"
    except ValueError:
        pass
