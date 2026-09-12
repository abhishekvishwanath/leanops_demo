from datetime import datetime, timezone

from app.services.followup import check_can_send, due_followup_days

CREATED = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)


def days_later(n):
    from datetime import timedelta
    return CREATED + timedelta(days=n)


def test_no_followups_due_before_day_3():
    due = due_followup_days(CREATED, days_later(2), "New", set())
    assert due == []


def test_day_3_due_once_elapsed():
    due = due_followup_days(CREATED, days_later(3), "New", set())
    assert due == [3]


def test_day_3_and_7_both_due_if_gap_was_missed():
    due = due_followup_days(CREATED, days_later(8), "Follow-up due", set())
    assert due == [3, 7]


def test_already_sent_days_are_excluded():
    due = due_followup_days(CREATED, days_later(8), "Follow-up due", {3})
    assert due == [7]


def test_stopped_on_terminal_status():
    due = due_followup_days(CREATED, days_later(10), "Appointment Booked", set())
    assert due == []


def test_stopped_on_reply():
    due = due_followup_days(CREATED, days_later(10), "New", set(), has_replied=True)
    assert due == []


def test_check_can_send_rejects_duplicate_day():
    ok, reason = check_can_send("New", 3, {3})
    assert not ok
    assert reason == "already_sent_for_this_day"


def test_check_can_send_rejects_invalid_day():
    ok, reason = check_can_send("New", 5, set())
    assert not ok
    assert "invalid_day" in reason


def test_check_can_send_rejects_stopped_status():
    ok, reason = check_can_send("Dead", 3, set())
    assert not ok
    assert "sequence_stopped" in reason


def test_check_can_send_rejects_after_reply():
    ok, reason = check_can_send("New", 3, set(), has_replied=True)
    assert not ok
    assert "replied" in reason


def test_check_can_send_allows_valid_new_day():
    ok, reason = check_can_send("Follow-up due", 7, {3})
    assert ok
    assert reason == "ok"
