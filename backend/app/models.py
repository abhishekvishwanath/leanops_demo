"""
SQLAlchemy models mirroring db/migrations/0001_init.sql and
0002_whatsapp_messages.sql. Column-for-column — this file has no independent
authority over the schema; the SQL migrations are the source of truth (see
CLAUDE.md).
"""
from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Time,
    DateTime,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    project_id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    project_name = Column(String, nullable=False)
    locality = Column(String, nullable=False)
    city = Column(String, nullable=False)
    construction_status = Column(String, nullable=False)
    rera_number = Column(String, nullable=False)
    possession = Column(String, nullable=False)
    total_floors = Column(Integer, nullable=False)
    amenity_count = Column(Integer, nullable=False)
    view = Column(String, nullable=False)
    parking_included = Column(Boolean, nullable=False)
    last_updated_at = Column(DateTime(timezone=True), nullable=False)
    updated_by = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    approved_for_ai = Column(Boolean, nullable=False)
    record_status = Column(String, nullable=False)


class ProjectUnitRow(Base):
    __tablename__ = "project_units"

    unit_id = Column(BigInteger, primary_key=True)
    project_id = Column(String, ForeignKey("projects.project_id"), nullable=False)
    bhk = Column(String, nullable=False)
    carpet_sqft = Column(Integer, nullable=False)
    base_price_inr = Column(BigInteger, nullable=False)
    image_url = Column(String)
    last_updated_at = Column(DateTime(timezone=True), nullable=False)
    updated_by = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    approved_for_ai = Column(Boolean, nullable=False)
    record_status = Column(String, nullable=False)
    stale_note = Column(Text)


class Salesperson(Base):
    __tablename__ = "salespeople"

    salesperson_id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    languages = Column(ARRAY(String), nullable=False)
    territory = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)
    active = Column(Boolean, nullable=False)
    role = Column(String, nullable=False)


class SalespersonProject(Base):
    __tablename__ = "salesperson_projects"

    salesperson_id = Column(String, ForeignKey("salespeople.salesperson_id"), primary_key=True)
    project_id = Column(String, ForeignKey("projects.project_id"), primary_key=True)


class Lead(Base):
    __tablename__ = "leads"

    lead_id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String)
    source = Column(String, nullable=False)
    project_interest = Column(String, ForeignKey("projects.project_id"))
    bhk = Column(String)
    budget_min_inr = Column(BigInteger)
    budget_max_inr = Column(BigInteger)
    preferred_localities = Column(String)
    language = Column(String)
    timeline = Column(String)
    last_intent = Column(Text)
    lead_grade = Column(String)
    lead_score = Column(Integer)
    created_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False)
    assigned_salesperson_id = Column(String, ForeignKey("salespeople.salesperson_id"))

    lead_type = Column(String, nullable=False, default="direct")
    broker_id = Column(String)
    broker_name = Column(String)
    source_partner = Column(String)
    ownership_start = Column(DateTime(timezone=True))
    ownership_expiry = Column(DateTime(timezone=True))
    commission_category = Column(String)
    claim_status = Column(String)
    duplicate_of = Column(String, ForeignKey("leads.lead_id"))
    canonical_lead_id = Column(String, ForeignKey("leads.lead_id"))


class LeadEvent(Base):
    __tablename__ = "lead_events"

    event_id = Column(BigInteger, primary_key=True)
    lead_id = Column(String, ForeignKey("leads.lead_id"), nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False)


class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"

    slot_id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    slot_date = Column(Date, nullable=False)
    slot_time = Column(Time, nullable=False)
    salesperson_id = Column(String, ForeignKey("salespeople.salesperson_id"), nullable=False)
    project_id = Column(String, ForeignKey("projects.project_id"), nullable=False)
    status = Column(String, nullable=False, default="Available")
    lead_id = Column(String, ForeignKey("leads.lead_id"))
    last_updated_at = Column(DateTime(timezone=True), nullable=False)
    updated_by = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    approved_for_ai = Column(Boolean, nullable=False)


class Faq(Base):
    __tablename__ = "faqs"

    faq_id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    category = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    approved_answer = Column(Text, nullable=False)
    last_updated_at = Column(DateTime(timezone=True), nullable=False)
    updated_by = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    approved_for_ai = Column(Boolean, nullable=False)
    record_status = Column(String, nullable=False)


class EscalationTicket(Base):
    __tablename__ = "escalation_tickets"

    ticket_id = Column(BigInteger, primary_key=True)
    tenant_id = Column(String, nullable=False)
    lead_id = Column(String, ForeignKey("leads.lead_id"), nullable=False)
    escalation_class = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    expert_type = Column(String)
    owner = Column(String)
    priority = Column(String)
    sla_due_at = Column(DateTime(timezone=True))
    status = Column(String, nullable=False, default="Open")
    resolution = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False)


class CallTranscript(Base):
    __tablename__ = "call_transcripts"

    call_id = Column(BigInteger, primary_key=True)
    tenant_id = Column(String, nullable=False)
    lead_id = Column(String, ForeignKey("leads.lead_id"), nullable=False)
    salesperson_id = Column(String, ForeignKey("salespeople.salesperson_id"))
    channel = Column(String, nullable=False)
    language = Column(String)
    transcript = Column(Text)
    recording_metadata = Column(JSON, default=dict)
    disposition = Column(String)
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))


class QualityReview(Base):
    __tablename__ = "quality_reviews"

    review_id = Column(BigInteger, primary_key=True)
    call_id = Column(BigInteger, ForeignKey("call_transcripts.call_id"), nullable=False)
    disclosure_pass = Column(Boolean, nullable=False)
    language_pass = Column(Boolean, nullable=False)
    qualification_pass = Column(Boolean, nullable=False)
    accuracy_pass = Column(Boolean, nullable=False)
    conversation_pass = Column(Boolean, nullable=False)
    escalation_pass = Column(Boolean, nullable=False)
    crm_pass = Column(Boolean, nullable=False)
    booking_pass = Column(Boolean, nullable=False)
    compliance_pass = Column(Boolean, nullable=False)
    hallucination_flag = Column(Boolean, nullable=False, default=False)
    reviewer = Column(String, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False)


class MediaAsset(Base):
    __tablename__ = "media_assets"

    media_id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.project_id"), nullable=False)
    type = Column(String, nullable=False)
    language = Column(String, nullable=False)
    url = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    approval_status = Column(String, nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_until = Column(DateTime(timezone=True))
    checksum = Column(String)


class WorkflowRule(Base):
    __tablename__ = "workflow_rules"

    workflow_id = Column(String, primary_key=True)
    trigger_event = Column(String, nullable=False)
    channel_or_role = Column(String, nullable=False)
    action = Column(Text, nullable=False)
    output = Column(String, nullable=False)
    sla_or_timing = Column(String, nullable=False)


class WhatsAppMessageRow(Base):
    __tablename__ = "whatsapp_messages"

    message_id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    lead_id = Column(String, ForeignKey("leads.lead_id"))
    salesperson_id = Column(String, ForeignKey("salespeople.salesperson_id"))
    to_phone = Column(String, nullable=False)
    direction = Column(String, nullable=False, default="outbound")
    template_name = Column(String, nullable=False)
    language = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    media_urls = Column(ARRAY(String), nullable=False, default=list)
    status = Column(String, nullable=False, default="queued")
    provider = Column(String, nullable=False, default="mock")
    provider_message_id = Column(String)
    created_at = Column(DateTime(timezone=True), nullable=False)
