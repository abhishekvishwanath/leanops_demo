"""
Duplicate/broker-lead detection per spec section 4.

Hard match: exact normalized phone -> auto-merge (the caller still creates a
record, linked via duplicate_of/canonical_lead_id, so no source event or
consent history is lost — see spec: "never silently delete records").

Soft matches -> review queue, never auto-merged:
  - email (case-insensitive exact)
  - name (case-insensitive exact) + last-4 phone digits
  - same source + same project_interest within a recency window
"""
from datetime import timedelta
from typing import List, Optional

from app.domain import DedupeResult, LeadCandidate
from app.services.phone import last4

SOFT_MATCH_WINDOW_HOURS = 24


def find_duplicate(
    *,
    phone: str,
    email: Optional[str],
    name: str,
    source: str,
    project_interest: Optional[str],
    created_at,
    candidates: List[LeadCandidate],
) -> DedupeResult:
    # Only compare against canonical leads (not other duplicates), so chains
    # always resolve to a single root record.
    canonical = [c for c in candidates if c.duplicate_of is None]

    for c in canonical:
        if c.phone == phone:
            return DedupeResult(match_type="hard", matched_lead=c, reason="exact_phone_match")

    if email:
        email_lower = email.strip().lower()
        for c in canonical:
            if c.email and c.email.strip().lower() == email_lower:
                return DedupeResult(match_type="soft", matched_lead=c, reason="email_match")

    name_lower = (name or "").strip().lower()
    phone_last4 = last4(phone)
    if name_lower and phone_last4:
        for c in canonical:
            if c.name.strip().lower() == name_lower and last4(c.phone) == phone_last4:
                return DedupeResult(match_type="soft", matched_lead=c, reason="name_and_last4_match")

    if project_interest:
        window_start = created_at - timedelta(hours=SOFT_MATCH_WINDOW_HOURS)
        for c in canonical:
            if (
                c.source == source
                and c.project_interest == project_interest
                and window_start <= c.created_at <= created_at
            ):
                return DedupeResult(
                    match_type="soft", matched_lead=c, reason="recent_source_project_match"
                )

    return DedupeResult(match_type="none")
