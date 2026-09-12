from datetime import date, datetime, time

from app.domain import SlotRecord
from app.services.scheduling import check_cancelable, check_confirmable, check_holdable

NOW = datetime(2026, 9, 12, 10, 0)


def make_slot(**overrides):
    base = dict(
        slot_id="SL001", project_id="PRJ003", salesperson_id="SP001",
        slot_date=date(2026, 9, 13), slot_time=time(11, 0),
        status="Available", lead_id=None, approved_for_ai=True,
    )
    base.update(overrides)
    return SlotRecord(**base)


def test_available_future_slot_is_holdable():
    result = check_holdable(make_slot(), NOW)
    assert result.ok


def test_already_held_slot_is_not_holdable():
    result = check_holdable(make_slot(status="Held", lead_id="LD0001"), NOW)
    assert not result.ok


def test_past_slot_is_not_holdable():
    result = check_holdable(make_slot(slot_date=date(2026, 9, 10)), NOW)
    assert not result.ok
    assert "past" in result.reason


def test_stale_unapproved_slot_is_not_holdable():
    result = check_holdable(make_slot(approved_for_ai=False), NOW)
    assert not result.ok


def test_held_slot_confirmable_by_its_own_lead():
    slot = make_slot(status="Held", lead_id="LD0001")
    result = check_confirmable(slot, "LD0001", NOW)
    assert result.ok


def test_held_slot_not_confirmable_by_a_different_lead():
    slot = make_slot(status="Held", lead_id="LD0001")
    result = check_confirmable(slot, "LD0002", NOW)
    assert not result.ok
    assert result.reason == "slot_held_for_a_different_lead"


def test_available_slot_not_confirmable_without_a_hold_first():
    result = check_confirmable(make_slot(status="Available"), "LD0001", NOW)
    assert not result.ok


def test_available_and_held_slots_are_cancelable():
    assert check_cancelable(make_slot(status="Available")).ok
    assert check_cancelable(make_slot(status="Held")).ok


def test_terminal_slots_are_not_cancelable():
    assert not check_cancelable(make_slot(status="Cancelled")).ok
    assert not check_cancelable(make_slot(status="Completed")).ok
