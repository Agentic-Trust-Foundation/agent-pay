from decimal import Decimal
from uuid import uuid4

import pytest

from agent_pay.webhook_resolution import ProviderEventResolver


def test_invalid_event_is_rejected():
    class Conn:
        def execute(self, *args):
            class Result:
                def fetchone(self):
                    return ('RECEIVED', False)
            return Result()

    with pytest.raises(PermissionError):
        ProviderEventResolver(Conn()).resolve(
            event_id=uuid4(), provider_operation_id=uuid4(), outcome='SUCCEEDED',
            provider_reference='ref', customer_ledger_account_id=uuid4(),
            clearing_ledger_account_id=uuid4())
