from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from agent_pay.authorization import AuthorizationContext, AuthorizationError


def context(**overrides):
    values = dict(
        evidence_id="ev-1",
        issuer="atf",
        agent_id="agent-1",
        account_id="account-1",
        scope=frozenset({"PAYMENT"}),
        max_amount=Decimal("100"),
        currency="USD",
        valid_until=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    values.update(overrides)
    return AuthorizationContext(**values)


def test_authorization_accepts_matching_payment():
    context().validate(agent_id="agent-1", account_id="account-1", amount=Decimal("50"), currency="USD")


@pytest.mark.parametrize("kwargs", [
    {"agent_id": "other", "account_id": "account-1", "amount": Decimal("50"), "currency": "USD"},
    {"agent_id": "agent-1", "account_id": "other", "amount": Decimal("50"), "currency": "USD"},
    {"agent_id": "agent-1", "account_id": "account-1", "amount": Decimal("101"), "currency": "USD"},
    {"agent_id": "agent-1", "account_id": "account-1", "amount": Decimal("50"), "currency": "EUR"},
])
def test_authorization_fails_closed(kwargs):
    with pytest.raises(AuthorizationError):
        context().validate(**kwargs)


def test_expired_authorization_fails_closed():
    with pytest.raises(AuthorizationError, match="expired"):
        context(valid_until=datetime.now(timezone.utc) - timedelta(seconds=1)).validate(
            agent_id="agent-1", account_id="account-1", amount=Decimal("1"), currency="USD"
        )
