from datetime import datetime, timezone

from app.services.escalation import classify_risk, compute_sla_due_at


def test_e1_discount_request():
    result = classify_risk("Can you give me a discount and reserve the unit for me?")
    assert result.escalation_class == "E1"


def test_e2_specific_unit_question():
    result = classify_risk("Which floor is unit number 704 on, and is it available?")
    assert result.escalation_class == "E2"


def test_e3_loan_question():
    result = classify_risk("What is the home loan eligibility and EMI for this flat?")
    assert result.escalation_class == "E3"


def test_e4_legal_question():
    result = classify_risk("Does the RERA agreement cover compensation for delay in possession?")
    assert result.escalation_class == "E4"


def test_e5_complaint_takes_priority_over_sales_keywords():
    # contains both a discount ask (E1) and a harassment complaint (E5) —
    # severity must win
    result = classify_risk("Your agent was rude, this is harassment, also can I get a discount?")
    assert result.escalation_class == "E5"


def test_no_risk_keywords_returns_none():
    assert classify_risk("What amenities does this project have?") is None


def test_sla_minutes_based_class():
    now = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)
    due = compute_sla_due_at("E1", now)
    assert due == datetime(2026, 9, 12, 10, 15, tzinfo=timezone.utc)


def test_sla_same_business_day_before_cutoff():
    now = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)
    due = compute_sla_due_at("E3", now)
    assert due == datetime(2026, 9, 12, 18, 0, tzinfo=timezone.utc)


def test_sla_same_business_day_after_cutoff_rolls_to_next_day():
    now = datetime(2026, 9, 12, 19, 0, tzinfo=timezone.utc)
    due = compute_sla_due_at("E4", now)
    assert due == datetime(2026, 9, 13, 18, 0, tzinfo=timezone.utc)


def test_e5_sla_is_immediate():
    now = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)
    assert compute_sla_due_at("E5", now) == now


def test_e0_has_no_sla():
    now = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)
    assert compute_sla_due_at("E0", now) is None
