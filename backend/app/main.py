from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app import followups, repositories
from app.booking import cancel_slot, confirm_slot, hold_slot
from app.db import get_db
from app.pipeline import run_capture_pipeline
from app.schemas import (
    ContactOutcomeRequest,
    DueFollowupOut,
    FollowupSendRequest,
    LeadCaptureRequest,
    LeadDetailResponse,
    LeadOut,
    LeadPipelineResponse,
    ReplyRequest,
    SlotActionRequest,
    SlotActionResponse,
    SlotCancelRequest,
    SlotOut,
)

app = FastAPI(title="XYZ Properties Lead Conversion Demo API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/leads", response_model=LeadPipelineResponse)
def capture_lead(payload: LeadCaptureRequest, db: Session = Depends(get_db)):
    """
    Entry point for WF001-WF006: normalize + dedupe + (qualify + match +
    assign + mock-contact). Mirrors an inbound webhook from Meta/website/
    WhatsApp/telephony.
    """
    return run_capture_pipeline(db, payload)


@app.get("/leads", response_model=list[LeadOut])
def get_leads(
    status: Optional[str] = None,
    project_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return repositories.list_leads(db, status=status, project_id=project_id)


@app.get("/leads/{lead_id}", response_model=LeadDetailResponse)
def get_lead(lead_id: str, db: Session = Depends(get_db)):
    result = repositories.get_lead_with_events(db, lead_id)
    if not result:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadDetailResponse(lead=result["lead"], events=result["events"])


# ---------------------------------------------------------------------------
# Scheduling (WF008)
# ---------------------------------------------------------------------------


@app.get("/projects/{project_id}/slots", response_model=list[SlotOut])
def get_slots(
    project_id: str,
    status: Optional[str] = None,
    slot_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return repositories.list_slots(db, project_id=project_id, status=status, slot_date=slot_date)


def _slot_action_or_409(result):
    if not result.ok:
        raise HTTPException(status_code=409, detail=result.reason)
    return SlotActionResponse(ok=result.ok, reason=result.reason)


@app.post("/slots/{slot_id}/hold", response_model=SlotActionResponse)
def hold(slot_id: str, payload: SlotActionRequest, db: Session = Depends(get_db)):
    """AI offers this slot to the lead — the pre-confirmation step of WF008."""
    return _slot_action_or_409(hold_slot(db, slot_id, payload.lead_id))


@app.post("/slots/{slot_id}/confirm", response_model=SlotActionResponse)
def confirm(slot_id: str, payload: SlotActionRequest, db: Session = Depends(get_db)):
    """Lead confirmed — books the slot only now, and only if it's still held for them."""
    return _slot_action_or_409(confirm_slot(db, slot_id, payload.lead_id))


@app.post("/slots/{slot_id}/cancel", response_model=SlotActionResponse)
def cancel(slot_id: str, payload: SlotCancelRequest, db: Session = Depends(get_db)):
    return _slot_action_or_409(cancel_slot(db, slot_id, payload.reason))


# ---------------------------------------------------------------------------
# Follow-up sequencing (WF009/WF010)
# ---------------------------------------------------------------------------


@app.get("/follow-ups/due", response_model=list[DueFollowupOut])
def get_due_followups(db: Session = Depends(get_db)):
    """
    What a scheduler (Celery beat / Trigger.dev in production) would act on
    right now. Read-only — call POST /leads/{id}/follow-up to actually send.
    """
    return followups.list_due(db)


@app.post("/leads/{lead_id}/follow-up", response_model=SlotActionResponse)
def send_followup(lead_id: str, payload: FollowupSendRequest, db: Session = Depends(get_db)):
    ok, reason, _contact_result = followups.send(db, lead_id, payload.day)
    if not ok:
        status_code = 404 if reason == "lead_not_found" else 409
        raise HTTPException(status_code=status_code, detail=reason)
    return SlotActionResponse(ok=True, reason=reason)


@app.post("/leads/{lead_id}/contact-outcome", response_model=SlotActionResponse)
def contact_outcome(lead_id: str, payload: ContactOutcomeRequest, db: Session = Depends(get_db)):
    """WF009 — logs the call disposition and, on no-answer, fires the immediate WhatsApp + retry task."""
    if not followups.record_contact_outcome(db, lead_id, payload.outcome, payload.channel):
        raise HTTPException(status_code=404, detail="lead_not_found")
    return SlotActionResponse(ok=True, reason="recorded")


@app.post("/leads/{lead_id}/opt-out", response_model=SlotActionResponse)
def opt_out(lead_id: str, db: Session = Depends(get_db)):
    if not followups.record_opt_out(db, lead_id):
        raise HTTPException(status_code=404, detail="lead_not_found")
    return SlotActionResponse(ok=True, reason="opted_out")


@app.post("/leads/{lead_id}/reply", response_model=SlotActionResponse)
def reply(lead_id: str, payload: ReplyRequest, db: Session = Depends(get_db)):
    if not followups.record_reply(db, lead_id, payload.message):
        raise HTTPException(status_code=404, detail="lead_not_found")
    return SlotActionResponse(ok=True, reason="reply_recorded")
