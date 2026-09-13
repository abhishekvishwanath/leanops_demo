"""
Orchestrates WF001-WF006 for a single inbound lead capture:
capture -> dedupe -> (qualify -> match -> assign -> contact-mock).

Hard-match duplicates are auto-merged into the canonical lead (still creating
a linked record, never overwriting/deleting) and short-circuit before
qualify/match/assign. Soft matches land in a review queue and also
short-circuit — spec section 4 requires a human to resolve uncertain
matches, so the pipeline correctly stops rather than guessing.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app import repositories, whatsapp_service
from app.domain import AssignmentResult
from app.schemas import AssignmentOut, LeadCaptureRequest, LeadPipelineResponse, MatchOut
from app.services import assignment, contact, dedupe, matching, qualify, whatsapp_templates
from app.services.phone import normalize_phone


def run_capture_pipeline(db: Session, payload: LeadCaptureRequest) -> LeadPipelineResponse:
    now = datetime.now(timezone.utc)
    normalized_phone = normalize_phone(payload.phone)
    candidates = repositories.get_all_lead_candidates(db)

    dedupe_result = dedupe.find_duplicate(
        phone=normalized_phone,
        email=payload.email,
        name=payload.name,
        source=payload.source,
        project_interest=payload.project_interest,
        created_at=now,
        candidates=candidates,
    )
    lead_id = repositories.next_lead_id(db)

    if dedupe_result.match_type == "hard":
        return _handle_hard_match(db, lead_id, payload, normalized_phone, now, dedupe_result)

    if dedupe_result.match_type == "soft":
        return _handle_soft_match(db, lead_id, payload, normalized_phone, now, dedupe_result)

    return _run_full_pipeline(db, lead_id, payload, normalized_phone, now)


def _handle_hard_match(db, lead_id, payload, normalized_phone, now, dedupe_result) -> LeadPipelineResponse:
    canonical = dedupe_result.matched_lead
    has_broker_claim = bool(payload.broker_id or payload.source_partner)
    claim_status = "Under Review" if has_broker_claim and payload.source != canonical.source else None
    status = "Merged - Broker Claim Under Review" if claim_status else "Merged - Duplicate"

    repositories.insert_lead(
        db,
        dict(
            lead_id=lead_id,
            name=payload.name,
            phone=normalized_phone,
            email=payload.email,
            source=payload.source,
            project_interest=payload.project_interest or canonical.project_interest,
            created_at=now,
            status=status,
            lead_type="broker_referred" if has_broker_claim else "direct",
            broker_id=payload.broker_id,
            broker_name=payload.broker_name,
            source_partner=payload.source_partner,
            claim_status=claim_status,
            duplicate_of=canonical.lead_id,
            canonical_lead_id=canonical.lead_id,
        ),
    )
    repositories.insert_event(db, lead_id, "lead.created", {"source": payload.source})
    repositories.insert_event(
        db, lead_id, "duplicate.flagged",
        {"match_type": "hard_match_phone", "canonical_lead_id": canonical.lead_id},
    )
    repositories.insert_event(
        db, canonical.lead_id, "lead.merged",
        {
            "merged_lead_id": lead_id,
            "reason": "broker ownership claim conflicts with existing lead"
            if claim_status else "exact phone match auto-merged",
            "claim_status": claim_status,
        },
    )
    db.commit()

    return LeadPipelineResponse(
        lead_id=lead_id,
        status=status,
        dedupe_match_type="hard",
        dedupe_reason=dedupe_result.reason,
        canonical_lead_id=canonical.lead_id,
        events=["lead.created", "duplicate.flagged", "lead.merged (on canonical)"],
    )


def _handle_soft_match(db, lead_id, payload, normalized_phone, now, dedupe_result) -> LeadPipelineResponse:
    matched = dedupe_result.matched_lead
    repositories.insert_lead(
        db,
        dict(
            lead_id=lead_id,
            name=payload.name,
            phone=normalized_phone,
            email=payload.email,
            source=payload.source,
            project_interest=payload.project_interest,
            bhk=payload.bhk,
            budget_min_inr=payload.budget_min_inr,
            budget_max_inr=payload.budget_max_inr,
            preferred_localities=payload.preferred_localities,
            language=payload.language,
            timeline=payload.timeline,
            created_at=now,
            status="Review Queue",
            duplicate_of=matched.lead_id,
            canonical_lead_id=None,
        ),
    )
    repositories.insert_event(db, lead_id, "lead.created", {"source": payload.source})
    repositories.insert_event(
        db, lead_id, "duplicate.flagged",
        {"match_type": "soft_match", "reason": dedupe_result.reason, "candidate_lead_id": matched.lead_id},
    )
    db.commit()

    return LeadPipelineResponse(
        lead_id=lead_id,
        status="Review Queue",
        dedupe_match_type="soft",
        dedupe_reason=dedupe_result.reason,
        canonical_lead_id=None,
        events=["lead.created", "duplicate.flagged"],
    )


def _run_full_pipeline(db, lead_id, payload, normalized_phone, now) -> LeadPipelineResponse:
    qualified = qualify.extract_fields(payload.model_dump())
    qualified = qualify.score_lead(qualified, payload.source)

    units = repositories.get_active_units(db, project_id=payload.project_interest)
    matches = matching.match_inventory(qualified, payload.project_interest, units)
    target_project = payload.project_interest or (matches[0].project_id if matches else None)

    assignment_result = AssignmentResult(salesperson_id=None, reason="no_project_identified")
    if target_project:
        owners = repositories.get_owners_for_project(db, target_project)
        specialists = repositories.get_specialists(db)
        workload_ids = [o.salesperson_id for o in owners] + [s.salesperson_id for s in specialists]
        workload = repositories.get_workload(db, workload_ids)
        assignment_result = assignment.assign_salesperson(
            language=qualified.language,
            project_id=target_project,
            owners=owners,
            specialists=specialists,
            workload=workload,
        )

    contact_result = contact.mock_contact(consent=payload.consent, language=qualified.language)
    status = "Assigned" if assignment_result.salesperson_id else "New"

    if payload.consent:
        whatsapp_service.send(
            db,
            whatsapp_templates.initial_acknowledgement(
                to_phone=normalized_phone, name=payload.name, language=qualified.language or "English"
            ),
            lead_id=lead_id,
        )

    repositories.insert_lead(
        db,
        dict(
            lead_id=lead_id,
            name=payload.name,
            phone=normalized_phone,
            email=payload.email,
            source=payload.source,
            project_interest=target_project,
            bhk=qualified.bhk,
            budget_min_inr=qualified.budget_min_inr,
            budget_max_inr=qualified.budget_max_inr,
            preferred_localities=qualified.preferred_localities,
            language=qualified.language,
            timeline=qualified.timeline,
            lead_grade=qualified.lead_grade,
            lead_score=qualified.lead_score,
            created_at=now,
            status=status,
            assigned_salesperson_id=assignment_result.salesperson_id,
        ),
    )

    events_created = ["lead.created", "lead.qualified"]
    repositories.insert_event(db, lead_id, "lead.created", {"source": payload.source})
    repositories.insert_event(
        db, lead_id, "lead.qualified",
        {
            "confidence": qualified.confidence,
            "lead_score": qualified.lead_score,
            "lead_grade": qualified.lead_grade,
        },
    )
    if matches:
        repositories.insert_event(
            db, lead_id, "property.matched", {"matches": [m.project_id for m in matches]}
        )
        events_created.append("property.matched")
        if payload.consent:
            top = matches[0]
            media_urls = repositories.get_media_urls_for_project(db, top.project_id)
            whatsapp_service.send(
                db,
                whatsapp_templates.property_match(
                    to_phone=normalized_phone, name=payload.name, project_name=top.project_name,
                    bhk=top.bhk, base_price_inr=top.base_price_inr, media_urls=media_urls,
                    language=qualified.language or "English",
                ),
                lead_id=lead_id,
            )
            events_created.append("whatsapp.sent (property_match)")
    if assignment_result.salesperson_id:
        repositories.insert_event(
            db, lead_id, "lead.assigned",
            {"salesperson_id": assignment_result.salesperson_id, "reason": assignment_result.reason},
        )
        events_created.append("lead.assigned")
    if assignment_result.language_gap:
        repositories.insert_event(
            db, lead_id, "assignment.language_gap_unresolved", {"reason": assignment_result.reason}
        )
        events_created.append("assignment.language_gap_unresolved")
    repositories.insert_event(db, lead_id, "contact.attempted", contact_result)
    events_created.append("contact.attempted")

    db.commit()

    return LeadPipelineResponse(
        lead_id=lead_id,
        status=status,
        dedupe_match_type="none",
        qualification={
            "bhk": qualified.bhk,
            "budget_min_inr": qualified.budget_min_inr,
            "budget_max_inr": qualified.budget_max_inr,
            "language": qualified.language,
            "timeline": qualified.timeline,
            "confidence": qualified.confidence,
            "lead_score": qualified.lead_score,
            "lead_grade": qualified.lead_grade,
        },
        matches=[MatchOut(**m.__dict__) for m in matches],
        assignment=AssignmentOut(
            salesperson_id=assignment_result.salesperson_id,
            reason=assignment_result.reason,
            language_gap=assignment_result.language_gap,
        ),
        contact=contact_result,
        events=events_created,
    )
