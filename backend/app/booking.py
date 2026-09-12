"""
Orchestrates WF008 (offer -> confirm -> reminder) on top of
app/services/scheduling.py's validation rules and repositories.py's atomic
compare-and-swap. Two-phase by design: `hold` is the AI "offering" a slot,
`confirm` is booking it only after the lead has actually said yes — matching
the spec's "book only after confirmation."
"""
from datetime import datetime

from sqlalchemy.orm import Session

from app import repositories
from app.domain import SlotActionResult
from app.services import scheduling


def hold_slot(db: Session, slot_id: str, lead_id: str) -> SlotActionResult:
    slot = repositories.get_slot(db, slot_id)
    if not slot:
        return SlotActionResult(False, "slot_not_found")
    if not repositories.get_lead(db, lead_id):
        return SlotActionResult(False, "lead_not_found")

    check = scheduling.check_holdable(slot, datetime.now())
    if not check.ok:
        return check

    won = repositories.cas_slot_status(
        db, slot_id,
        expected_status="Available", expected_lead_id=None,
        new_status="Held", lead_id=lead_id,
    )
    if not won:
        return SlotActionResult(False, "lost_race_slot_no_longer_available")

    repositories.insert_event(
        db, lead_id, "appointment.offered",
        {"slot_id": slot_id, "project_id": slot.project_id,
         "date": str(slot.slot_date), "time": str(slot.slot_time)},
    )
    db.commit()
    return SlotActionResult(True, "held")


def confirm_slot(db: Session, slot_id: str, lead_id: str) -> SlotActionResult:
    slot = repositories.get_slot(db, slot_id)
    if not slot:
        return SlotActionResult(False, "slot_not_found")

    check = scheduling.check_confirmable(slot, lead_id, datetime.now())
    if not check.ok:
        return check

    won = repositories.cas_slot_status(
        db, slot_id,
        expected_status="Held", expected_lead_id=lead_id,
        new_status="Booked", lead_id=lead_id,
    )
    if not won:
        return SlotActionResult(False, "slot_state_changed_before_confirmation")

    repositories.update_lead_status(db, lead_id, "Appointment Booked")
    repositories.insert_event(
        db, lead_id, "appointment.booked",
        {"slot_id": slot_id, "project_id": slot.project_id,
         "date": str(slot.slot_date), "time": str(slot.slot_time)},
    )
    repositories.insert_event(
        db, lead_id, "appointment.reminder_scheduled",
        {"note": "Mock reminder — real WhatsApp/SMS reminder delivery pending Phase 6 credentials."},
    )
    db.commit()
    return SlotActionResult(True, "booked")


def cancel_slot(db: Session, slot_id: str, reason: str) -> SlotActionResult:
    slot = repositories.get_slot(db, slot_id)
    if not slot:
        return SlotActionResult(False, "slot_not_found")

    check = scheduling.check_cancelable(slot)
    if not check.ok:
        return check

    cancelled = repositories.cancel_slot_row(db, slot_id)
    if not cancelled:
        return SlotActionResult(False, "slot_state_changed_before_cancellation")

    if slot.lead_id:
        repositories.insert_event(
            db, slot.lead_id, "appointment.cancelled", {"slot_id": slot_id, "reason": reason}
        )
        lead = repositories.get_lead(db, slot.lead_id)
        if lead and lead.status == "Appointment Booked":
            repositories.update_lead_status(db, slot.lead_id, "Assigned")

    db.commit()
    return SlotActionResult(True, "cancelled")
