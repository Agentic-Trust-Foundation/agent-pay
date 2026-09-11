from datetime import datetime, timedelta, timezone

import pytest

from agent_pay.webhooks import _enforce_replay_window


def test_replay_window_disabled_by_default(monkeypatch):
    monkeypatch.delenv("AGENT_PAY_WEBHOOK_REPLAY_WINDOW_SECONDS", raising=False)
    _enforce_replay_window({})


def test_replay_window_accepts_recent_event(monkeypatch):
    monkeypatch.setenv("AGENT_PAY_WEBHOOK_REPLAY_WINDOW_SECONDS", "300")
    timestamp = datetime.now(timezone.utc).isoformat()
    _enforce_replay_window({"occurred_at": timestamp})


def test_replay_window_rejects_stale_event(monkeypatch):
    monkeypatch.setenv("AGENT_PAY_WEBHOOK_REPLAY_WINDOW_SECONDS", "300")
    timestamp = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    with pytest.raises(Exception, match="outside replay window"):
        _enforce_replay_window({"occurred_at": timestamp})
