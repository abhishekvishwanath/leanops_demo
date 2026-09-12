from app.services.qualify import extract_fields, score_lead


def test_extract_uses_structured_fields_at_full_confidence():
    payload = {
        "bhk": "2BHK",
        "budget_min_inr": 6500000,
        "budget_max_inr": 14000000,
        "language": "English",
        "timeline": "0-3 months",
        "preferred_localities": "Ghatkopar",
    }
    fields = extract_fields(payload)
    assert fields.bhk == "2BHK"
    assert fields.confidence == 1.0


def test_extract_falls_back_to_message_parsing():
    payload = {"message": "Looking for a 2BHK around 90 lakh, Hindi preferred, ready to move"}
    fields = extract_fields(payload)
    assert fields.bhk == "2BHK"
    assert fields.budget_min_inr == 9_000_000
    assert fields.language == "Hindi"
    assert fields.timeline == "0-3 months"
    assert 0 < fields.confidence <= 1.0


def test_extract_message_with_no_recognizable_fields_has_zero_confidence():
    fields = extract_fields({"message": "hello, just browsing"})
    assert fields.bhk is None
    assert fields.confidence == 0.0


def test_score_lead_high_intent():
    payload = {
        "bhk": "2BHK", "budget_min_inr": 12_000_000, "budget_max_inr": 13_000_000,
        "timeline": "0-3 months",
    }
    fields = extract_fields(payload)
    scored = score_lead(fields, source="Incoming Call")
    assert scored.lead_grade == "A"
    assert scored.lead_score >= 70


def test_score_lead_low_intent():
    fields = extract_fields({"message": "just curious"})
    scored = score_lead(fields, source="Meta Lead Ads")
    assert scored.lead_grade == "C"


def test_score_is_clamped_to_100():
    payload = {
        "bhk": "2BHK", "budget_min_inr": 12_000_000, "budget_max_inr": 12_500_000,
        "timeline": "0-3 months",
    }
    fields = extract_fields(payload)
    scored = score_lead(fields, source="Incoming Call")
    assert scored.lead_score <= 100
