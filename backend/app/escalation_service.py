"""
Orchestrates spec section 5's escalation classification for an inbound
question tied to a lead:

  1. Try an approved-FAQ match first (E0 — "AI answers from fresh ERP/FAQ").
  2. If nothing routine matched, run the risk keyword scan (E1-E5).
  3. If neither matched, default to E1 rather than silently dropping the
     question — every question gets either an approved answer or a human
     owner, never neither.

E1/E2 tickets default their owner to the lead's assigned salesperson (or the
project's owner, if the lead isn't assigned yet) since those classes are
handled by the sales/inventory side of the same team. E3/E4/E5 don't have a
person to default to yet (no finance/legal/supervisor roster exists) — the
dashboard's "assign expert" action (spec section 3) fills that in manually.

Known limitation of FAQ-first ordering: a message can overlap an approved
FAQ's wording while actually needing escalation (e.g. "What's my home loan
EMI eligibility for this flat?" bag-of-words-matches FAQ003, "Can you
arrange a home loan?"). This was a deliberate choice, not an oversight: every
approved FAQ answer in the seed data is written defensively (it defers
specifics to a human/lender rather than inventing numbers), so a false-
positive FAQ match still returns a safe, non-substantive answer — it just
skips creating a ticket for a human to follow up on the specific ask. If
FAQ content ever stops being that conservative, or ticket coverage matters
more than answer latency, flip the order (classify_risk before
find_best_match) instead of patching this comment.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app import repositories
from app.domain import ClassificationResult
from app.services import escalation
from app.services.escalation import ESCALATION_RULES
from app.services.faq import find_best_match


def _default_owner(db: Session, lead, escalation_class: str) -> Optional[str]:
    if escalation_class not in ("E1", "E2"):
        return None
    if lead.assigned_salesperson_id:
        return lead.assigned_salesperson_id
    if lead.project_interest:
        owners = repositories.get_owners_for_project(db, lead.project_interest)
        if owners:
            return owners[0].salesperson_id
    return None


def handle_question(db: Session, lead_id: str, message: str) -> Optional[dict]:
    lead = repositories.get_lead(db, lead_id)
    if not lead:
        return None

    now = datetime.now(timezone.utc)
    faqs = repositories.get_active_faqs(db)
    faq_match = find_best_match(message, faqs)

    if faq_match:
        classification = ClassificationResult(
            escalation_class="E0", confidence=faq_match.score, source="faq_match", faq=faq_match
        )
    else:
        classification = escalation.classify_risk(message) or ClassificationResult(
            escalation_class="E1",
            confidence=0.3,
            source="unclassified_default",
            matched_keywords=[],
        )

    rule = ESCALATION_RULES[classification.escalation_class]

    if rule.ai_may_answer:
        repositories.insert_event(
            db, lead_id, "question.answered_e0",
            {"message": message, "faq_id": faq_match.faq_id, "confidence": classification.confidence},
        )
        db.commit()
        return {
            "escalation_class": "E0",
            "confidence": classification.confidence,
            "source": classification.source,
            "ai_answer": faq_match.answer,
            "escalation_ticket_id": None,
        }

    sla_due_at = escalation.compute_sla_due_at(classification.escalation_class, now)
    owner = _default_owner(db, lead, classification.escalation_class)

    ticket_id = repositories.create_escalation_ticket(
        db,
        lead_id=lead_id,
        escalation_class=classification.escalation_class,
        reason=message,
        expert_type=rule.expert_type,
        owner=owner,
        priority=rule.priority,
        sla_due_at=sla_due_at,
        created_at=now,
    )
    repositories.insert_event(
        db, lead_id, "escalation.created",
        {
            "ticket_id": ticket_id,
            "escalation_class": classification.escalation_class,
            "source": classification.source,
            "matched_keywords": classification.matched_keywords,
        },
    )

    if rule.pause_automation:
        repositories.update_lead_status(db, lead_id, "Escalated - Human Takeover")

    db.commit()
    return {
        "escalation_class": classification.escalation_class,
        "confidence": classification.confidence,
        "source": classification.source,
        "ai_answer": None,
        "escalation_ticket_id": ticket_id,
    }
