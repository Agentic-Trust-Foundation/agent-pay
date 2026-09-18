from agent_pay.outbox_worker import AUDITABLE_EVENTS


def test_financial_events_are_auditable():
    assert "PaymentSucceeded" in AUDITABLE_EVENTS
    assert "PaymentFailed" in AUDITABLE_EVENTS
    assert "PaymentOutcomeUnknown" in AUDITABLE_EVENTS


def test_notification_is_a_non_financial_side_effect():
    assert "NotificationRequested" not in AUDITABLE_EVENTS
