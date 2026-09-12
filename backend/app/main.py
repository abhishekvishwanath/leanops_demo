from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app import repositories
from app.db import get_db
from app.pipeline import run_capture_pipeline
from app.schemas import LeadCaptureRequest, LeadDetailResponse, LeadOut, LeadPipelineResponse

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
