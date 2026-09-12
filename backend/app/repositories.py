"""
Thin data-access layer: converts ORM rows <-> the plain dataclasses in
app.domain, so app/services/* never has to know about SQLAlchemy. Also owns
lead_id generation and the handful of write paths the pipeline needs.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain import LeadCandidate, ProjectUnit, SalespersonRecord
from app.models import (
    Lead,
    LeadEvent,
    Project,
    ProjectUnitRow,
    Salesperson,
    SalespersonProject,
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
