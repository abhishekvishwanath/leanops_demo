from datetime import datetime, timedelta, timezone

from app.domain import LeadCandidate
from app.services.dedupe import find_duplicate

NOW = datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)


def make_candidate(**overrides):
    base = dict(
        lead_id="LD0001",
        phone="+919810001001",
        email="rohan.mehta@example.com",
        name="Rohan Mehta",
        source="Meta Lead Ads",
        project_interest="PRJ003",
        created_at=NOW - timedelta(hours=2),
        duplicate_of=None,
        canonical_lead_id=None,
    )
    base.update(overrides)
    return LeadCandidate(**base)


def test_hard_match_on_exact_phone():
    result = find_duplicate(
        phone="+919810001001", email="different@example.com", name="Someone Else",
        source="Website Form", project_interest="PRJ003", created_at=NOW,
        candidates=[make_candidate()],
    )
    assert result.match_type == "hard"
    assert result.matched_lead.lead_id == "LD0001"


def test_hard_match_never_matches_against_a_non_canonical_row():
    # a lead that is itself already a flagged duplicate must not become a
    # dedupe target — only canonical rows can be matched against
    dup_row = make_candidate(lead_id="LD0011", duplicate_of="LD0001")
    result = find_duplicate(
        phone="+919810001001", email=None, name="X", source="Website Form",
        project_interest=None, created_at=NOW, candidates=[dup_row],
    )
    assert result.match_type == "none"


def test_soft_match_on_email():
    result = find_duplicate(
        phone="+919999999999", email="ROHAN.MEHTA@example.com", name="Someone Else",
        source="Website Form", project_interest=None, created_at=NOW,
        candidates=[make_candidate()],
    )
    assert result.match_type == "soft"
    assert result.reason == "email_match"


def test_soft_match_on_name_and_last4():
    result = find_duplicate(
        phone="+911111001001", email=None, name="Rohan Mehta",
        source="Website Form", project_interest=None, created_at=NOW,
        candidates=[make_candidate()],
    )
    assert result.match_type == "soft"
    assert result.reason == "name_and_last4_match"


def test_soft_match_on_recent_source_project_combo():
    result = find_duplicate(
        phone="+919999999999", email=None, name="Someone Else",
        source="Meta Lead Ads", project_interest="PRJ003", created_at=NOW,
        candidates=[make_candidate()],
    )
    assert result.match_type == "soft"
    assert result.reason == "recent_source_project_match"


def test_recent_source_project_combo_outside_window_is_not_a_match():
    old_candidate = make_candidate(created_at=NOW - timedelta(hours=48))
    result = find_duplicate(
        phone="+919999999999", email=None, name="Someone Else",
        source="Meta Lead Ads", project_interest="PRJ003", created_at=NOW,
        candidates=[old_candidate],
    )
    assert result.match_type == "none"


def test_no_match():
    result = find_duplicate(
        phone="+919999999999", email="new@example.com", name="Nobody Known",
        source="WhatsApp", project_interest="PRJ010", created_at=NOW,
        candidates=[make_candidate()],
    )
    assert result.match_type == "none"
