"""
WF006 — "Assign salesperson by project, territory, language, workload."

Priority order:
  1. The project's owning salesperson, if they speak the lead's language.
  2. A floating language specialist who speaks it (project ownership for
     inventory questions stays with the owner — see SYNTHETIC_ADDITIONS.md
     patch #2 for why this role exists).
  3. The project owner anyway, best-effort, flagged as an unresolved
     language gap so it surfaces on the escalation/dashboard side rather
     than silently mis-routing the lead.
  4. Nobody owns the project at all -> no assignment (shouldn't happen with
     real data, but handled rather than raising).

Within any tied group, the candidate with the lowest current workload wins.
"""
from typing import Dict, List, Optional

from app.domain import AssignmentResult, SalespersonRecord


def _pick_lowest_workload(
    candidates: List[SalespersonRecord], workload: Dict[str, int]
) -> SalespersonRecord:
    return min(candidates, key=lambda c: workload.get(c.salesperson_id, 0))


def assign_salesperson(
    *,
    language: Optional[str],
    project_id: Optional[str],
    owners: List[SalespersonRecord],
    specialists: List[SalespersonRecord],
    workload: Dict[str, int],
) -> AssignmentResult:
    owner_candidates = [o for o in owners if o.active and project_id in o.projects]

    if not owner_candidates:
        return AssignmentResult(salesperson_id=None, reason="no_owner_found")

    if language:
        language_matched_owners = [o for o in owner_candidates if language in o.languages]
        if language_matched_owners:
            pick = _pick_lowest_workload(language_matched_owners, workload)
            return AssignmentResult(salesperson_id=pick.salesperson_id, reason="project_owner_language_match")

        matched_specialists = [s for s in specialists if s.active and language in s.languages]
        if matched_specialists:
            pick = _pick_lowest_workload(matched_specialists, workload)
            return AssignmentResult(
                salesperson_id=pick.salesperson_id,
                reason="floating_specialist_language_override",
            )

    pick = _pick_lowest_workload(owner_candidates, workload)
    return AssignmentResult(
        salesperson_id=pick.salesperson_id,
        reason="project_owner_language_gap_unresolved",
        language_gap=bool(language),
    )
