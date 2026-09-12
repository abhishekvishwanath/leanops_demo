"""
Executive funnel aggregation (spec section 3, "Executive funnel"). Pure
function over plain status strings so it's testable without a database.
"""
from collections import Counter
from typing import List

# Buckets are deliberately coarser than the raw `status` column — the
# executive funnel wants stage counts, not every internal status string.
FUNNEL_BUCKETS = {
    "New": "new",
    "Review Queue": "review_queue",
    "Nurture": "nurture",
    "Assigned": "contacted",
    "Sales callback": "contacted",
    "Follow-up due": "contacted",
    "WhatsApp follow-up": "contacted",
    "Qualified": "qualified",
    "Appointment proposed": "appointment_offered",
    "Appointment Booked": "appointment_booked",
    "Escalated - Human Takeover": "escalated",
    "Opted Out": "opted_out",
    "Dead": "dead",
    "Merged - Duplicate": "merged",
    "Merged - Broker Claim Under Review": "merged",
}


def compute_funnel(statuses: List[str]) -> dict:
    counts = Counter()
    for status in statuses:
        bucket = FUNNEL_BUCKETS.get(status, "other")
        counts[bucket] += 1
    total = len(statuses)
    result = {bucket: 0 for bucket in set(FUNNEL_BUCKETS.values())}
    result.update(counts)
    result["total"] = total
    return result
