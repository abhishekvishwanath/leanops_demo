"""
WF003 — "Select matching project/unit records from ERP using hard filters."

Hard filters (must match, or the unit is excluded entirely): approved_for_ai
(caller must pre-filter these — see repositories.get_active_units),
project_interest (if given), BHK (if given), budget range (if given).
Locality is treated as a ranking boost rather than a hard filter, since
free-text locality wording rarely matches the ERP field exactly.
"""
import re
from typing import List, Optional

from app.domain import MatchResult, ProjectUnit, QualifiedFields

TOP_N = 3


def _locality_matches(preferred_localities: str, project_locality: str) -> bool:
    """
    preferred_localities is free text like "Ghatkopar / Vikhroli" — check
    whether any of its tokens appears in the project's locality (e.g.
    "Ghatkopar" in "Ghatkopar East"), not the other way around.
    """
    tokens = [t.strip().lower() for t in re.split(r"[/,]", preferred_localities) if t.strip()]
    locality_lower = project_locality.lower()
    return any(token in locality_lower for token in tokens)


def match_inventory(
    fields: QualifiedFields,
    project_interest: Optional[str],
    units: List[ProjectUnit],
) -> List[MatchResult]:
    candidates = units

    if project_interest:
        candidates = [u for u in candidates if u.project_id == project_interest]

    if fields.bhk:
        candidates = [u for u in candidates if u.bhk == fields.bhk]

    if fields.budget_min_inr and fields.budget_max_inr:
        candidates = [
            u for u in candidates
            if fields.budget_min_inr <= u.base_price_inr <= fields.budget_max_inr
        ]

    results = []
    for u in candidates:
        score = 50
        reasons = ["bhk_match" if fields.bhk else "no_bhk_filter"]

        if fields.preferred_localities and _locality_matches(fields.preferred_localities, u.locality):
            score += 30
            reasons.append("locality_match")

        if fields.budget_min_inr and fields.budget_max_inr:
            midpoint = (fields.budget_min_inr + fields.budget_max_inr) / 2
            if midpoint and abs(u.base_price_inr - midpoint) / midpoint <= 0.10:
                score += 20
                reasons.append("price_near_budget_midpoint")

        results.append(
            MatchResult(
                project_id=u.project_id,
                project_name=u.project_name,
                bhk=u.bhk,
                base_price_inr=u.base_price_inr,
                score=score,
                reasons=reasons,
            )
        )

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:TOP_N]
