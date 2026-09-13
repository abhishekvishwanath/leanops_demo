"""
Plain dataclasses shared by the pipeline services. Kept independent of the
ORM/SQLAlchemy layer so services/* can be unit tested with in-memory data —
no database required. app/repositories.py is responsible for converting
ORM rows into these types and back.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class LeadCandidate:
    """A previously-captured lead, used as a dedupe comparison target."""
    lead_id: str
    phone: str
    email: Optional[str]
    name: str
    source: str
    project_interest: Optional[str]
    created_at: datetime
    duplicate_of: Optional[str]
    canonical_lead_id: Optional[str]


@dataclass
class DedupeResult:
    match_type: str  # "hard" | "soft" | "none"
    matched_lead: Optional[LeadCandidate] = None
    reason: str = ""


@dataclass
class QualifiedFields:
    bhk: Optional[str] = None
    budget_min_inr: Optional[int] = None
    budget_max_inr: Optional[int] = None
    language: Optional[str] = None
    timeline: Optional[str] = None
    preferred_localities: Optional[str] = None
    confidence: float = 1.0
    lead_score: int = 0
    lead_grade: str = "C"


@dataclass
class ProjectUnit:
    project_id: str
    project_name: str
    locality: str
    city: str
    bhk: str
    carpet_sqft: int
    base_price_inr: int
    approved_for_ai: bool


@dataclass
class MatchResult:
    project_id: str
    project_name: str
    bhk: str
    base_price_inr: int
    score: int
    reasons: list = field(default_factory=list)


@dataclass
class SalespersonRecord:
    salesperson_id: str
    name: str
    languages: list
    territory: str
    projects: list
    active: bool
    role: str  # "project_owner" | "floating_specialist"


@dataclass
class AssignmentResult:
    salesperson_id: Optional[str]
    reason: str
    language_gap: bool = False


@dataclass
class SlotRecord:
    slot_id: str
    project_id: str
    salesperson_id: str
    slot_date: object  # datetime.date
    slot_time: object  # datetime.time
    status: str
    lead_id: Optional[str]
    approved_for_ai: bool


@dataclass
class SlotActionResult:
    ok: bool
    reason: str


@dataclass
class FaqRecord:
    faq_id: str
    category: str
    question: str
    approved_answer: str


@dataclass
class FaqMatch:
    faq_id: str
    question: str
    answer: str
    score: float


@dataclass
class ClassificationResult:
    escalation_class: str  # "E0".."E5"
    confidence: float
    source: str  # "faq_match" | "risk_keywords" | "unclassified_default"
    matched_keywords: list = field(default_factory=list)
    faq: Optional[FaqMatch] = None


@dataclass
class WhatsAppMessage:
    """A fully-composed WhatsApp message, ready to send. Building this is
    real production logic (spec section 7/8 templates); only the actual
    network call that dispatches it is mocked (see app/whatsapp_service.py)."""
    to_phone: str
    template_name: str
    language: str
    body: str
    media_urls: list = field(default_factory=list)
