"""
WF008 — "Offer available slots, book only after confirmation, send
reminder." and spec section 6 — "recheck availability before booking...
price/availability/possession/slot changes should invalidate cached answers
immediately."

This module only holds the *validation* rules (is this slot still holdable/
confirmable right now). The atomic compare-and-swap DB update that actually
prevents a race between two leads grabbing the same slot lives in
repositories.py (an UPDATE ... WHERE status = 'Available' RETURNING), since
that has to happen at the database, not in Python.
"""
from datetime import date, datetime, time
from typing import Optional

from app.domain import SlotActionResult, SlotRecord


def _slot_datetime(slot_date: date, slot_time: time) -> datetime:
    return datetime.combine(slot_date, slot_time)


def check_holdable(slot: SlotRecord, now: datetime) -> SlotActionResult:
    if not slot.approved_for_ai:
        return SlotActionResult(False, "slot_not_approved_for_ai")
    if slot.status != "Available":
        return SlotActionResult(False, f"slot_not_available (status={slot.status})")
    if _slot_datetime(slot.slot_date, slot.slot_time) <= now:
        return SlotActionResult(False, "slot_in_the_past")
    return SlotActionResult(True, "ok")


def check_confirmable(slot: SlotRecord, lead_id: str, now: datetime) -> SlotActionResult:
    if slot.status != "Held":
        return SlotActionResult(False, f"slot_not_held (status={slot.status})")
    if slot.lead_id != lead_id:
        return SlotActionResult(False, "slot_held_for_a_different_lead")
    if _slot_datetime(slot.slot_date, slot.slot_time) <= now:
        return SlotActionResult(False, "slot_in_the_past")
    return SlotActionResult(True, "ok")


def check_cancelable(slot: SlotRecord) -> SlotActionResult:
    if slot.status in ("Cancelled", "Completed"):
        return SlotActionResult(False, f"slot_already_terminal (status={slot.status})")
    return SlotActionResult(True, "ok")
