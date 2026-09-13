"""
Thin data-access layer: converts ORM rows <-> the plain dataclasses in
app.domain, so app/services/* never has to know about SQLAlchemy. Also owns
lead_id generation and the handful of write paths the pipeline needs.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.domain import FaqRecord, LeadCandidate, ProjectUnit, SalespersonRecord, SlotRecord
from app.models import (
    AppointmentSlot,
    CallTranscript,
    EscalationTicket,
    Faq,
    Lead,
    LeadEvent,
    MediaAsset,
    Project,
    ProjectUnitRow,
    QualityReview,
    Salesperson,
    SalespersonProject,
    WhatsAppMessageRow,
)

TENANT_ID = "00000000-0000-0000-0000-000000000001"
CLOSED_STATUSES = {"Dead", "Nurture"}


def next_lead_id(db: Session) -> str:
    existing = db.scalars(select(Lead.lead_id)).all()
    max_n = 0
    for lead_id in existing:
        try:
            max_n = max(max_n, int(lead_id.lstrip("LD")))
        except ValueError:
            continue
    return f"LD{max_n + 1:04d}"


def get_all_lead_candidates(db: Session) -> List[LeadCandidate]:
    rows = db.scalars(select(Lead)).all()
    return [
        LeadCandidate(
            lead_id=r.lead_id,
            phone=r.phone,
            email=r.email,
            name=r.name,
            source=r.source,
            project_interest=r.project_interest,
            created_at=r.created_at,
            duplicate_of=r.duplicate_of,
            canonical_lead_id=r.canonical_lead_id,
        )
        for r in rows
    ]


def get_active_units(db: Session, project_id: Optional[str] = None) -> List[ProjectUnit]:
    stmt = (
        select(ProjectUnitRow, Project)
        .join(Project, Project.project_id == ProjectUnitRow.project_id)
        .where(ProjectUnitRow.approved_for_ai.is_(True))
        .where(ProjectUnitRow.record_status == "active")
        .where(Project.approved_for_ai.is_(True))
        .where(Project.record_status == "active")
    )
    if project_id:
        stmt = stmt.where(ProjectUnitRow.project_id == project_id)

    rows = db.execute(stmt).all()
    return [
        ProjectUnit(
            project_id=unit.project_id,
            project_name=project.project_name,
            locality=project.locality,
            city=project.city,
            bhk=unit.bhk,
            carpet_sqft=unit.carpet_sqft,
            base_price_inr=unit.base_price_inr,
            approved_for_ai=unit.approved_for_ai,
        )
        for unit, project in rows
    ]


def get_owners_for_project(db: Session, project_id: str) -> List[SalespersonRecord]:
    stmt = (
        select(Salesperson)
        .join(SalespersonProject, SalespersonProject.salesperson_id == Salesperson.salesperson_id)
        .where(SalespersonProject.project_id == project_id)
    )
    rows = db.scalars(stmt).all()
    return [_to_salesperson_record(db, r) for r in rows]


def get_specialists(db: Session) -> List[SalespersonRecord]:
    rows = db.scalars(select(Salesperson).where(Salesperson.role == "floating_specialist")).all()
    return [_to_salesperson_record(db, r) for r in rows]


def _to_salesperson_record(db: Session, sp: Salesperson) -> SalespersonRecord:
    project_ids = db.scalars(
        select(SalespersonProject.project_id).where(
            SalespersonProject.salesperson_id == sp.salesperson_id
        )
    ).all()
    return SalespersonRecord(
        salesperson_id=sp.salesperson_id,
        name=sp.name,
        languages=list(sp.languages or []),
        territory=sp.territory,
        projects=list(project_ids),
        active=sp.active,
        role=sp.role,
    )


def get_workload(db: Session, salesperson_ids: List[str]) -> Dict[str, int]:
    if not salesperson_ids:
        return {}
    stmt = (
        select(Lead.assigned_salesperson_id, func.count(Lead.lead_id))
        .where(Lead.assigned_salesperson_id.in_(salesperson_ids))
        .where(Lead.status.notin_(CLOSED_STATUSES))
        .group_by(Lead.assigned_salesperson_id)
    )
    return dict(db.execute(stmt).all())


def insert_lead(db: Session, lead_fields: dict) -> None:
    db.add(Lead(tenant_id=TENANT_ID, **lead_fields))


def insert_event(db: Session, lead_id: str, event_type: str, payload: dict) -> None:
    db.add(
        LeadEvent(
            lead_id=lead_id,
            event_type=event_type,
            payload=payload,
            created_at=datetime.now(timezone.utc),
        )
    )


def get_lead_with_events(db: Session, lead_id: str) -> Optional[dict]:
    lead = db.get(Lead, lead_id)
    if not lead:
        return None
    events = db.scalars(
        select(LeadEvent).where(LeadEvent.lead_id == lead_id).order_by(LeadEvent.created_at)
    ).all()
    return {
        "lead": lead,
        "events": [
            {"event_type": e.event_type, "payload": e.payload, "created_at": e.created_at}
            for e in events
        ],
    }


def list_leads(
    db: Session, status: Optional[str] = None, project_id: Optional[str] = None
) -> List[Lead]:
    stmt = select(Lead)
    if status:
        stmt = stmt.where(Lead.status == status)
    if project_id:
        stmt = stmt.where(Lead.project_interest == project_id)
    return db.scalars(stmt.order_by(Lead.created_at)).all()


# ---------------------------------------------------------------------------
# Scheduling (Phase 3)
# ---------------------------------------------------------------------------


def _slot_to_record(row: AppointmentSlot) -> SlotRecord:
    return SlotRecord(
        slot_id=row.slot_id,
        project_id=row.project_id,
        salesperson_id=row.salesperson_id,
        slot_date=row.slot_date,
        slot_time=row.slot_time,
        status=row.status,
        lead_id=row.lead_id,
        approved_for_ai=row.approved_for_ai,
    )


def get_slot(db: Session, slot_id: str) -> Optional[SlotRecord]:
    row = db.get(AppointmentSlot, slot_id)
    return _slot_to_record(row) if row else None


def list_slots(
    db: Session,
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    slot_date: Optional[str] = None,
) -> List[SlotRecord]:
    stmt = select(AppointmentSlot)
    if project_id:
        stmt = stmt.where(AppointmentSlot.project_id == project_id)
    if status:
        stmt = stmt.where(AppointmentSlot.status == status)
    if slot_date:
        stmt = stmt.where(AppointmentSlot.slot_date == slot_date)
    rows = db.scalars(stmt.order_by(AppointmentSlot.slot_date, AppointmentSlot.slot_time)).all()
    return [_slot_to_record(r) for r in rows]


def cas_slot_status(
    db: Session,
    slot_id: str,
    *,
    expected_status: str,
    expected_lead_id: Optional[str],
    new_status: str,
    lead_id: Optional[str],
) -> bool:
    """
    Atomic compare-and-swap on a slot's status, so two concurrent requests
    can never both win the same slot (spec: "recheck availability before
    booking"). Returns True iff this call's WHERE clause actually matched a
    row — i.e. this caller won the race.
    """
    params = {
        "slot_id": slot_id,
        "expected_status": expected_status,
        "new_status": new_status,
        "lead_id": lead_id,
    }
    where_lead_clause = ""
    if expected_lead_id is not None:
        where_lead_clause = "and lead_id = :expected_lead_id"
        params["expected_lead_id"] = expected_lead_id

    result = db.execute(
        text(
            f"""
            update appointment_slots
            set status = :new_status,
                lead_id = :lead_id,
                version = version + 1,
                last_updated_at = now()
            where slot_id = :slot_id
              and status = :expected_status
              {where_lead_clause}
            """
        ),
        params,
    )
    return result.rowcount == 1


def cancel_slot_row(db: Session, slot_id: str) -> bool:
    result = db.execute(
        text(
            """
            update appointment_slots
            set status = 'Cancelled', version = version + 1, last_updated_at = now()
            where slot_id = :slot_id
              and status not in ('Cancelled', 'Completed')
            """
        ),
        {"slot_id": slot_id},
    )
    return result.rowcount == 1


def update_lead_status(db: Session, lead_id: str, status: str) -> None:
    db.execute(
        text("update leads set status = :status where lead_id = :lead_id"),
        {"status": status, "lead_id": lead_id},
    )


# ---------------------------------------------------------------------------
# Follow-up sequencing (Phase 3)
# ---------------------------------------------------------------------------


def get_lead(db: Session, lead_id: str) -> Optional[Lead]:
    return db.get(Lead, lead_id)


def get_sent_followup_days(db: Session, lead_id: str) -> set:
    rows = db.scalars(
        select(LeadEvent.payload).where(
            LeadEvent.lead_id == lead_id, LeadEvent.event_type == "followup.sent"
        )
    ).all()
    return {r["day"] for r in rows if r and "day" in r}


def has_replied(db: Session, lead_id: str) -> bool:
    return (
        db.scalar(
            select(func.count(LeadEvent.event_id)).where(
                LeadEvent.lead_id == lead_id, LeadEvent.event_type == "lead.replied"
            )
        )
        > 0
    )


def list_leads_for_followup_scan(db: Session) -> List[Lead]:
    """All leads that are still real pipeline participants (excludes
    already-merged duplicates/review-queue rows, which never enter the
    funnel to begin with)."""
    from app.services.followup import STOP_STATUSES

    stmt = select(Lead).where(Lead.status.notin_(STOP_STATUSES))
    return db.scalars(stmt).all()


# ---------------------------------------------------------------------------
# Escalation classification (Phase 4)
# ---------------------------------------------------------------------------


def get_active_faqs(db: Session) -> List[FaqRecord]:
    rows = db.scalars(
        select(Faq).where(Faq.approved_for_ai.is_(True), Faq.record_status == "active")
    ).all()
    return [
        FaqRecord(faq_id=r.faq_id, category=r.category, question=r.question, approved_answer=r.approved_answer)
        for r in rows
    ]


def create_escalation_ticket(
    db: Session,
    *,
    lead_id: str,
    escalation_class: str,
    reason: str,
    expert_type: Optional[str],
    owner: Optional[str],
    priority: Optional[str],
    sla_due_at,
    created_at,
) -> int:
    ticket = EscalationTicket(
        tenant_id=TENANT_ID,
        lead_id=lead_id,
        escalation_class=escalation_class,
        reason=reason,
        expert_type=expert_type,
        owner=owner,
        priority=priority,
        sla_due_at=sla_due_at,
        status="Open",
        created_at=created_at,
    )
    db.add(ticket)
    db.flush()
    return ticket.ticket_id


def list_escalations(
    db: Session,
    status: Optional[str] = None,
    escalation_class: Optional[str] = None,
    owner: Optional[str] = None,
) -> List[EscalationTicket]:
    stmt = select(EscalationTicket)
    if status:
        stmt = stmt.where(EscalationTicket.status == status)
    if escalation_class:
        stmt = stmt.where(EscalationTicket.escalation_class == escalation_class)
    if owner:
        stmt = stmt.where(EscalationTicket.owner == owner)
    return db.scalars(stmt.order_by(EscalationTicket.created_at.desc())).all()


def get_escalation(db: Session, ticket_id: int) -> Optional[EscalationTicket]:
    return db.get(EscalationTicket, ticket_id)


def update_escalation(db: Session, ticket_id: int, fields: dict) -> Optional[EscalationTicket]:
    ticket = db.get(EscalationTicket, ticket_id)
    if not ticket:
        return None
    for key, value in fields.items():
        if value is not None:
            setattr(ticket, key, value)
    return ticket


# ---------------------------------------------------------------------------
# Dashboard reads (Phase 5)
# ---------------------------------------------------------------------------


def list_projects(db: Session) -> List[Project]:
    return db.scalars(select(Project).order_by(Project.project_id)).all()


def get_project(db: Session, project_id: str) -> Optional[Project]:
    return db.get(Project, project_id)


def get_project_with_units(db: Session, project_id: str):
    project = db.get(Project, project_id)
    if not project:
        return None
    units = db.scalars(
        select(ProjectUnitRow).where(ProjectUnitRow.project_id == project_id)
    ).all()
    return {"project": project, "units": units}


def list_units_by_project(db: Session) -> Dict[str, list]:
    rows = db.scalars(select(ProjectUnitRow)).all()
    by_project: Dict[str, list] = {}
    for r in rows:
        by_project.setdefault(r.project_id, []).append(r)
    return by_project


def list_salespeople(db: Session) -> List[Salesperson]:
    return db.scalars(select(Salesperson).order_by(Salesperson.salesperson_id)).all()


def get_projects_for_salesperson(db: Session, salesperson_id: str) -> List[str]:
    return list(
        db.scalars(
            select(SalespersonProject.project_id).where(
                SalespersonProject.salesperson_id == salesperson_id
            )
        ).all()
    )


def get_all_workload(db: Session) -> Dict[str, int]:
    stmt = (
        select(Lead.assigned_salesperson_id, func.count(Lead.lead_id))
        .where(Lead.assigned_salesperson_id.isnot(None))
        .where(Lead.status.notin_(CLOSED_STATUSES))
        .group_by(Lead.assigned_salesperson_id)
    )
    return dict(db.execute(stmt).all())


def list_quality_reviews(db: Session) -> List[dict]:
    stmt = (
        select(QualityReview, CallTranscript)
        .join(CallTranscript, CallTranscript.call_id == QualityReview.call_id)
        .order_by(QualityReview.created_at.desc())
    )
    rows = db.execute(stmt).all()
    return [{"review": review, "call": call} for review, call in rows]


def get_all_lead_statuses(db: Session) -> List[str]:
    return list(db.scalars(select(Lead.status)).all())


def update_lead_fields(db: Session, lead_id: str, fields: dict) -> Optional[Lead]:
    lead = db.get(Lead, lead_id)
    if not lead:
        return None
    for key, value in fields.items():
        if value is not None:
            setattr(lead, key, value)
    return lead


# ---------------------------------------------------------------------------
# WhatsApp messaging (mocked provider — see app/whatsapp_service.py)
# ---------------------------------------------------------------------------


def get_salesperson(db: Session, salesperson_id: str) -> Optional[Salesperson]:
    return db.get(Salesperson, salesperson_id)


def get_media_urls_for_project(db: Session, project_id: str) -> List[str]:
    return list(
        db.scalars(select(MediaAsset.url).where(MediaAsset.project_id == project_id)).all()
    )


def insert_whatsapp_message(
    db: Session,
    *,
    message_id: str,
    lead_id: Optional[str],
    salesperson_id: Optional[str],
    to_phone: str,
    template_name: str,
    language: str,
    body: str,
    media_urls: list,
    status: str,
    provider: str,
    provider_message_id: Optional[str],
) -> None:
    db.add(
        WhatsAppMessageRow(
            message_id=message_id,
            tenant_id=TENANT_ID,
            lead_id=lead_id,
            salesperson_id=salesperson_id,
            to_phone=to_phone,
            template_name=template_name,
            language=language,
            body=body,
            media_urls=media_urls,
            status=status,
            provider=provider,
            provider_message_id=provider_message_id,
            created_at=datetime.now(timezone.utc),
        )
    )
