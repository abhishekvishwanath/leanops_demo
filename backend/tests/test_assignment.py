from app.domain import SalespersonRecord
from app.services.assignment import assign_salesperson

SP001 = SalespersonRecord("SP001", "Amit Verma", ["English", "Hindi"], "Central Mumbai", ["PRJ001", "PRJ002", "PRJ003", "PRJ010"], True, "project_owner")
SP004 = SalespersonRecord("SP004", "Divya Rao", ["English", "Hindi", "Marathi", "Kannada"], "Floating", [], True, "floating_specialist")


def test_owner_assigned_when_language_matches():
    result = assign_salesperson(
        language="English", project_id="PRJ003", owners=[SP001], specialists=[SP004], workload={},
    )
    assert result.salesperson_id == "SP001"
    assert result.reason == "project_owner_language_match"
    assert result.language_gap is False


def test_falls_back_to_floating_specialist_on_language_gap():
    result = assign_salesperson(
        language="Marathi", project_id="PRJ001", owners=[SP001], specialists=[SP004], workload={},
    )
    assert result.salesperson_id == "SP004"
    assert result.reason == "floating_specialist_language_override"


def test_best_effort_assigns_owner_when_no_specialist_covers_language():
    result = assign_salesperson(
        language="Kannada", project_id="PRJ010", owners=[SP001], specialists=[], workload={},
    )
    assert result.salesperson_id == "SP001"
    assert result.reason == "project_owner_language_gap_unresolved"
    assert result.language_gap is True


def test_no_owner_found_for_unowned_project():
    result = assign_salesperson(
        language="English", project_id="PRJ999", owners=[SP001], specialists=[SP004], workload={},
    )
    assert result.salesperson_id is None
    assert result.reason == "no_owner_found"


def test_workload_breaks_ties_among_language_matched_specialists():
    sp005 = SalespersonRecord("SP005", "Extra Specialist", ["Kannada"], "Floating", [], True, "floating_specialist")
    result = assign_salesperson(
        language="Kannada", project_id="PRJ010", owners=[SP001],
        specialists=[SP004, sp005], workload={"SP004": 5, "SP005": 1},
    )
    assert result.salesperson_id == "SP005"


def test_inactive_owner_is_excluded():
    inactive_owner = SalespersonRecord("SP002", "Inactive", ["English"], "West", ["PRJ004"], False, "project_owner")
    result = assign_salesperson(
        language="English", project_id="PRJ004", owners=[inactive_owner], specialists=[], workload={},
    )
    assert result.salesperson_id is None
    assert result.reason == "no_owner_found"
