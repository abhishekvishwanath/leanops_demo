"""
Orchestrates WF009/WF010. `list_due` and `send` are meant to be called by a
scheduler (Celery beat / Trigger.dev in production — see architecture notes
in CLAUDE.md); there is no in-process scheduler here, this is a demo.
`record_contact_outcome`, `record_opt_out`, and `record_reply` are the stop/
trigger conditions the sequence reacts to.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app import repositories
from app.services import followup
from app.services.contact import mock_contact


def list_due(db: Session) -> list[dict]:
    now = datetime.now(timezone.utc)
    due = []
    for lead in repositories.list_leads_for_followup_scan(db):
        sent_days = repositories.get_sent_followup_days(db, lead.lead_id)
        replied = repositories.has_replied(db, lead.lead_id)
        for day in followup.due_followup_days(lead.created_at, now, lead.status, sent_days, replied):
            due.append(
                {
                    "lead_id": lead.lead_id,
                    "day": day,
                    "days_since_created": followup.days_since(lead.created_at, now),
                }
            )
    return due


def send(db: Session, lead_id: str, day: int) -> tuple[bool, str, Optional[dict]]:
    lead = repositories.get_lead(db, lead_id)
    if not lead:
        return False, "lead_not_found", None

    sent_days = repositories.get_sent_followup_days(db, lead_id)
    replied = repositories.has_replied(db, lead_id)
    ok, reason = followup.check_can_send(lead.status, day, sent_days, replied)
    if not ok:
        return False, reason, None

    contact_result = mock_contact(consent=True, language=lead.language)
    repositories.insert_event(db, lead_id, "followup.sent", {"day": day, **contact_result})
    db.commit()
    return True, "sent", contact_result


def record_contact_outcome(db: Session, lead_id: str, outcome: str, channel: str) -> bool:
    lead = repositories.get_lead(db, lead_id)
    if not lead:
        return False

    repositories.insert_event(db, lead_id, f"call.{outcome}", {"channel": channel})
    if outcome == "no_answer":
        contact_result = mock_contact(consent=True, language=lead.language)
        repositories.insert_event(
            db, lead_id, "followup.sent", {"day": 0, "immediate": True, **contact_result}
        )
        repositories.insert_event(
            db, lead_id, "retry.task_created",
            {"note": "Retry contact attempt scheduled (mock) — real retry queue pending Phase 6."},
        )
    db.commit()
    return True


def record_opt_out(db: Session, lead_id: str) -> bool:
    if not repositories.get_lead(db, lead_id):
        return False
    repositories.update_lead_status(db, lead_id, "Opted Out")
    repositories.insert_event(db, lead_id, "optout.received", {})
    db.commit()
    return True


def record_reply(db: Session, lead_id: str, message: str) -> bool:
    if not repositories.get_lead(db, lead_id):
        return False
    repositories.insert_event(db, lead_id, "lead.replied", {"message": message})
    db.commit()
    return True
