"""
WF002 — "AI extracts language, locality, BHK, area, budget, timeline, intent."

No LLM/voice provider is wired up yet (Phase 6), so this is an explicit mock:
if the capture payload already carries structured fields (the normal case for
Meta/website forms with structured questions), we use them directly at full
confidence. If only a free-text `message` is given (the incoming-call/
WhatsApp free-text case), a small keyword/regex extractor stands in for the
real AI qualification call. Swap `extract_fields`'s fallback branch for a
real model call in Phase 6 without touching callers.
"""
import re
from typing import Optional

from app.domain import QualifiedFields

BHK_PATTERN = re.compile(r"\b([1-4])\s*BHK\b", re.IGNORECASE)
LAKH_CRORE_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(lakh|lakhs|crore|crores)", re.IGNORECASE
)
TIMELINE_KEYWORDS = [
    ("ready", "0-3 months"),
    ("immediate", "0-3 months"),
    ("0-3 month", "0-3 months"),
    ("3-6 month", "3-6 months"),
    ("6-12 month", "6-12 months"),
    ("next year", "6-12 months"),
]
KNOWN_LANGUAGES = ["English", "Hindi", "Marathi", "Kannada", "Telugu", "Gujarati"]


def _extract_from_message(message: str) -> QualifiedFields:
    message = message or ""
    fields = QualifiedFields()
    hits = 0
    total = 4  # bhk, budget, language, timeline

    bhk_match = BHK_PATTERN.search(message)
    if bhk_match:
        fields.bhk = f"{bhk_match.group(1)}BHK"
        hits += 1

    amounts = []
    for value, unit in LAKH_CRORE_PATTERN.findall(message):
        multiplier = 100_000 if unit.lower().startswith("lakh") else 10_000_000
        amounts.append(int(float(value) * multiplier))
    if amounts:
        fields.budget_min_inr = min(amounts)
        fields.budget_max_inr = max(amounts) if len(amounts) > 1 else int(min(amounts) * 1.2)
        hits += 1

    lower_message = message.lower()
    for lang in KNOWN_LANGUAGES:
        if lang.lower() in lower_message:
            fields.language = lang
            hits += 1
            break

    for keyword, timeline in TIMELINE_KEYWORDS:
        if keyword in lower_message:
            fields.timeline = timeline
            hits += 1
            break

    fields.confidence = round(hits / total, 2) if total else 0.0
    return fields


def extract_fields(payload: dict) -> QualifiedFields:
    structured_keys = ("bhk", "budget_min_inr", "budget_max_inr", "language", "timeline")
    has_structured = any(payload.get(k) for k in structured_keys)

    if has_structured:
        return QualifiedFields(
            bhk=payload.get("bhk"),
            budget_min_inr=payload.get("budget_min_inr"),
            budget_max_inr=payload.get("budget_max_inr"),
            language=payload.get("language"),
            timeline=payload.get("timeline"),
            preferred_localities=payload.get("preferred_localities"),
            confidence=1.0,
        )

    extracted = _extract_from_message(payload.get("message", ""))
    extracted.preferred_localities = payload.get("preferred_localities")
    return extracted


SOURCE_INTENT_BONUS = {
    "Incoming Call": 10,
    "WhatsApp": 5,
    "Website Form": 3,
    "Meta Lead Ads": 0,
}


def score_lead(fields: QualifiedFields, source: str) -> QualifiedFields:
    """Heuristic lead scoring (v0 — replace with a trained model later)."""
    score = 40

    if fields.bhk and fields.budget_min_inr and fields.budget_max_inr:
        score += 20

    if fields.timeline == "0-3 months":
        score += 15
    elif fields.timeline == "3-6 months":
        score += 8

    score += SOURCE_INTENT_BONUS.get(source, 0)

    if fields.budget_min_inr and fields.budget_max_inr and fields.budget_max_inr > 0:
        width_ratio = (fields.budget_max_inr - fields.budget_min_inr) / fields.budget_max_inr
        if width_ratio < 0.3:
            score += 10

    score = max(0, min(100, score))
    fields.lead_score = score
    fields.lead_grade = "A" if score >= 70 else "B" if score >= 50 else "C"
    return fields
