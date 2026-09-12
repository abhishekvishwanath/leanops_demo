from datetime import date, datetime, time
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


class SlotOut(BaseModel):
    slot_id: str
    project_id: str
    salesperson_id: str
    slot_date: date
    slot_time: time
    status: str
    lead_id: Optional[str]


class SlotActionRequest(BaseModel):
    lead_id: str


class SlotCancelRequest(BaseModel):
    reason: str = "Not specified"


class SlotActionResponse(BaseModel):
    ok: bool
    reason: str


class FollowupSendRequest(BaseModel):
    day: int


class DueFollowupOut(BaseModel):
    lead_id: str
    day: int
    days_since_created: int


class ContactOutcomeRequest(BaseModel):
    outcome: str  # "answered" | "no_answer"
    channel: str = "voice"


class ReplyRequest(BaseModel):
    message: str


class LeadDetailResponse(BaseModel):
    lead: LeadOut
    events: list[LeadEventOut]


class QuestionRequest(BaseModel):
    message: str


class QuestionResponse(BaseModel):
    escalation_class: str
    confidence: float
    source: str
    ai_answer: Optional[str] = None
    escalation_ticket_id: Optional[int] = None


class ClassifyRequest(BaseModel):
    message: str


class ClassifyResponse(BaseModel):
    escalation_class: str
    confidence: float
    source: str
    matched_keywords: list[str] = []


class EscalationTicketOut(BaseModel):
    ticket_id: int
    lead_id: str
    escalation_class: str
    reason: str
    expert_type: Optional[str]
    owner: Optional[str]
    priority: Optional[str]
    sla_due_at: Optional[datetime]
    status: str
    resolution: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class EscalationUpdateRequest(BaseModel):
    owner: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    resolution: Optional[str] = None


class ProjectUnitOut(BaseModel):
    unit_id: int
    bhk: str
    carpet_sqft: int
    base_price_inr: int
    image_url: Optional[str]
    approved_for_ai: bool
    record_status: str
    stale_note: Optional[str]

    class Config:
        from_attributes = True


class ProjectOut(BaseModel):
    project_id: str
    project_name: str
    locality: str
    city: str
    construction_status: str
    rera_number: str
    possession: str
    total_floors: int
    amenity_count: int
    view: str
    parking_included: bool
    approved_for_ai: bool
    record_status: str
    units: list[ProjectUnitOut] = []

    class Config:
        from_attributes = True


class SalespersonOut(BaseModel):
    salesperson_id: str
    name: str
    languages: list[str]
    territory: str
    phone: str
    email: str
    active: bool
    role: str
    projects: list[str] = []
    active_lead_count: int = 0

    class Config:
        from_attributes = True


class CallTranscriptOut(BaseModel):
    call_id: int
    lead_id: str
    salesperson_id: Optional[str]
    channel: str
    language: Optional[str]
    transcript: Optional[str]
    disposition: Optional[str]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True


class QualityReviewOut(BaseModel):
    review_id: int
    disclosure_pass: bool
    language_pass: bool
    qualification_pass: bool
    accuracy_pass: bool
    conversation_pass: bool
    escalation_pass: bool
    crm_pass: bool
    booking_pass: bool
    compliance_pass: bool
    hallucination_flag: bool
    reviewer: str
    notes: Optional[str]
    created_at: datetime
    call: CallTranscriptOut

    class Config:
        from_attributes = True


class LeadUpdateRequest(BaseModel):
    assigned_salesperson_id: Optional[str] = None
    status: Optional[str] = None
    last_intent: Optional[str] = None
