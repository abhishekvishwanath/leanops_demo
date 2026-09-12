from app.domain import ProjectUnit, QualifiedFields
from app.services.matching import match_inventory

UNITS = [
    ProjectUnit("PRJ003", "Metroview Enclave", "Ghatkopar East", "Mumbai", "2BHK", 665, 12_900_000, True),
    ProjectUnit("PRJ003", "Metroview Enclave", "Ghatkopar East", "Mumbai", "1BHK", 460, 8_900_000, True),
    ProjectUnit("PRJ002", "Lakeside Crest", "Powai", "Mumbai", "2BHK", 780, 15_000_000, True),
]


def test_hard_filter_by_bhk_and_budget():
    fields = QualifiedFields(bhk="2BHK", budget_min_inr=6_500_000, budget_max_inr=14_000_000)
    results = match_inventory(fields, project_interest=None, units=UNITS)
    project_ids = {r.project_id for r in results}
    assert project_ids == {"PRJ003"}  # PRJ002's 2BHK is over budget


def test_hard_filter_by_project_interest():
    fields = QualifiedFields(bhk="2BHK", budget_min_inr=1, budget_max_inr=99_000_000)
    results = match_inventory(fields, project_interest="PRJ002", units=UNITS)
    assert len(results) == 1
    assert results[0].project_id == "PRJ002"


def test_locality_match_boosts_score():
    fields = QualifiedFields(
        bhk="2BHK", budget_min_inr=6_500_000, budget_max_inr=16_000_000,
        preferred_localities="Ghatkopar / Vikhroli",
    )
    results = match_inventory(fields, project_interest=None, units=UNITS)
    top = results[0]
    assert top.project_id == "PRJ003"
    assert "locality_match" in top.reasons


def test_no_match_when_budget_excludes_everything():
    fields = QualifiedFields(bhk="2BHK", budget_min_inr=1, budget_max_inr=1000)
    results = match_inventory(fields, project_interest=None, units=UNITS)
    assert results == []


def test_stale_units_never_reach_matching_because_repo_pre_filters():
    # matching.py trusts its caller to only pass approved_for_ai units, per
    # repositories.get_active_units's WHERE clause — this test documents
    # that the function itself does no additional filtering.
    stale_only = [ProjectUnit("PRJ008", "Skyline 45", "Borivali East", "Mumbai", "1BHK", 490, 8_500_000, False)]
    fields = QualifiedFields(bhk="1BHK", budget_min_inr=7_000_000, budget_max_inr=9_000_000)
    results = match_inventory(fields, project_interest=None, units=stale_only)
    assert len(results) == 1  # would need to be excluded upstream, not here
