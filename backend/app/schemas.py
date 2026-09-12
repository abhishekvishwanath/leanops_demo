from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class LeadCaptureRequest(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    source: str  # "Meta Lead Ads" | "Website Form" | "WhatsApp" | "Incoming Call"
    consent: bool = True

    # Structured intake (preferred, e.g. from a web form)
    project_interest: Optional[str] = None
    bhk: Optional[str] = None
    budget_min_inr: Optional[int] = None
    budget_max_inr: Optional[int] = None
    preferred_localities: Optional[str] = None
    language: Optional[str] = None
    timeline: Optional[str] = None

    # Free-text fallback (e.g. a WhatsApp message or call transcript snippet)
    message: Optional[str] = None

    # Broker referral (optional)
    broker_id: Optional[str] = None
    broker_name: Optional[str] = None
    source_partner: Optional[str] = None


class MatchOut(BaseModel):
    project_id: str
    project_name: str
    bhk: str
    base_price_inr: int
    score: int
    reasons: list[str]


class AssignmentOut(BaseModel):
    salesperson_id: Optional[str]
    reason: str
    language_gap: bool = False


class LeadPipelineResponse(BaseModel):
    lead_id: str
    status: str
    dedupe_match_type: str
    dedupe_reason: Optional[str] = None
    canonical_lead_id: Optional[str] = None
    qualification: Optional[dict] = None
    matches: list[MatchOut] = []
    assignment: Optional[AssignmentOut] = None
    contact: Optional[dict] = None
    events: list[str] = []


class LeadOut(BaseModel):
    lead_id: str
    name: str
    phone: str
    email: Optional[str]
    source: str
    project_interest: Optional[str]
    bhk: Optional[str]
    budget_min_inr: Optional[int]
    budget_max_inr: Optional[int]
    language: Optional[str]
    timeline: Optional[str]
    lead_grade: Optional[str]
    lead_score: Optional[int]
    created_at: datetime
    status: str
    assigned_salesperson_id: Optional[str]
    duplicate_of: Optional[str]
    canonical_lead_id: Optional[str]
    claim_status: Optional[str]

    class Config:
        from_attributes = True


class LeadEventOut(BaseModel):
    event_type: str
    payload: Any
    created_at: datetime


class LeadDetailResponse(BaseModel):
    lead: LeadOut
    events: list[LeadEventOut]
