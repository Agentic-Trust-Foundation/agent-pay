from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from agent_pay.approval import ApprovalBinding, ApprovalError, ensure_pending


def test_approval_binding_is_deterministic():
    binding = ApprovalBinding("req-1", "acct-1", "agent-1", Decimal("25"), "usd", "merchant-1", "pv-1", "ev-1")
    assert binding.digest() == binding.digest()


def test_material_change_changes_binding():
    a = ApprovalBinding("req-1", "acct-1", "agent-1", Decimal("25"), "USD", "merchant-1", "pv-1", "ev-1")
    b = ApprovalBinding("req-1", "acct-1", "agent-1", Decimal("26"), "USD", "merchant-1", "pv-1", "ev-1")
    assert a.digest() != b.digest()


def test_expired_approval_is_rejected():
    with pytest.raises(ApprovalError, match="expired"):
        ensure_pending(status="PENDING", expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))


def test_terminal_approval_is_rejected():
    with pytest.raises(ApprovalError, match="no longer"):
        ensure_pending(status="APPROVED", expires_at=None)
