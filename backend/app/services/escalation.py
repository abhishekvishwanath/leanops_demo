"""
WF (stage 7, "Escalate") / spec section 5 — human escalation classification.

Real classification would be an LLM call (Phase 6); until then this is an
explicit keyword-based mock, checked in severity order (E5 down to E1) so a
message that trips multiple categories always routes to the more serious
one — a safety/complaint signal should never be masked by an unrelated
pricing question in the same message.

Class E0 (routine) is *not* decided here — see app/escalation_service.py,
which tries an approved-FAQ match first and only falls through to this
keyword scan if nothing routine matched.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from app.domain import ClassificationResult

E5_KEYWORDS = ["harassment", "threat", "refund", "urgent complaint", "incorrect claim", "scam", "abuse", "fraud"]
E4_KEYWORDS = ["title", "rera", "agreement", "dispute", "possession claim", "compensation for delay", "litigation", "sale deed"]
E3_KEYWORDS = ["loan eligibility", "emi", "sanction", "stamp duty", "statutory cost", "interest rate", "home loan", "tax"]
E2_KEYWORDS = ["specific unit", "which floor", "corner unit", "live availability", "payment plan", "unit number", "top floor", "ground floor"]
E1_KEYWORDS = ["discount", "negotiat", "final price", "reserve the unit", "reservation", "alternative project", "best price", "lower the price"]

_RISK_ORDER = [("E5", E5_KEYWORDS), ("E4", E4_KEYWORDS), ("E3", E3_KEYWORDS), ("E2", E2_KEYWORDS), ("E1", E1_KEYWORDS)]


@dataclass
class EscalationRule:
    expert_type: Optional[str]
    priority: Optional[str]
    sla_minutes: Optional[int]  # exact offset, e.g. 15 for E1
    sla_same_business_day: bool
    pause_automation: bool
    ai_may_answer: bool


ESCALATION_RULES = {
    "E0": EscalationRule(None, None, None, False, False, True),
    "E1": EscalationRule("Salesperson", "Medium", 15, False, False, False),
    "E2": EscalationRule("Inventory Manager", "High", 10, False, False, False),
    "E3": EscalationRule("Finance Partner", "Medium", None, True, False, False),
    "E4": EscalationRule("Legal/Compliance", "High", None, True, False, False),
    "E5": EscalationRule("Supervisor", "Critical", 0, False, True, False),
}


def classify_risk(message: str) -> Optional[ClassificationResult]:
    lower = message.lower()
    for escalation_class, keywords in _RISK_ORDER:
        matched = [k for k in keywords if k in lower]
        if matched:
            return ClassificationResult(
                escalation_class=escalation_class,
                confidence=0.9,
                source="risk_keywords",
                matched_keywords=matched,
            )
    return None


def compute_sla_due_at(escalation_class: str, now: datetime) -> Optional[datetime]:
    rule = ESCALATION_RULES[escalation_class]
    if rule.sla_minutes is not None:
        return now + timedelta(minutes=rule.sla_minutes)
    if rule.sla_same_business_day:
        end_of_day = now.replace(hour=18, minute=0, second=0, microsecond=0)
        return end_of_day if now < end_of_day else end_of_day + timedelta(days=1)
    return None
