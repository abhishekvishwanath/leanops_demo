"""
WF009/WF010 — no-answer retry + the day 3/7/10 follow-up sequence, stopping
on reply, opt-out, booking, human takeover, or dead status.

Pure calculation: given when a lead was created, its current status, and
which sequence days have already been sent, what's due "now"? The actual
sending (a job scheduler in production — Celery beat / Trigger.dev, per the
architecture) is out of scope here; a scheduler would just call
POST /leads/{id}/follow-up for whatever this function says is due.
"""
from datetime import datetime
from typing import List, Set

FOLLOWUP_DAYS = [3, 7, 10]

# Any of these lead statuses means the sequence has already ended for a real
# reason (booked, merged into another record, dead, opted out, parked in a
# review queue) — spec: "stop on reply, opt-out, appointment or dead status".
STOP_STATUSES = {
    "Appointment Booked",
    "Merged - Duplicate",
    "Merged - Broker Claim Under Review",
    "Review Queue",
    "Dead",
    "Opted Out",
}


def days_since(created_at: datetime, now: datetime) -> int:
    return (now - created_at).days


def due_followup_days(
    created_at: datetime,
    now: datetime,
    status: str,
    sent_days: Set[int],
    has_replied: bool = False,
) -> List[int]:
    if status in STOP_STATUSES or has_replied:
        return []
    elapsed = days_since(created_at, now)
    return [day for day in FOLLOWUP_DAYS if elapsed >= day and day not in sent_days]


def check_can_send(
    status: str, day: int, sent_days: Set[int], has_replied: bool = False
) -> tuple[bool, str]:
    if status in STOP_STATUSES:
        return False, f"sequence_stopped (status={status})"
    if has_replied:
        return False, "sequence_stopped (lead has replied)"
    if day not in FOLLOWUP_DAYS:
        return False, f"invalid_day (must be one of {FOLLOWUP_DAYS})"
    if day in sent_days:
        return False, "already_sent_for_this_day"
    return True, "ok"
