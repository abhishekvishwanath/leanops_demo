from app.domain import FaqRecord
from app.services.faq import find_best_match

FAQS = [
    FaqRecord("FAQ001", "Pricing", "Does the base price include registration and stamp duty?",
              "Base prices are exclusive of statutory costs."),
    FaqRecord("FAQ002", "Site Visit", "Can I visit on Sunday?",
              "Sunday visits are available only for selected projects."),
    FaqRecord("FAQ003", "Loans", "Can you arrange a home loan?",
              "We can connect you with lending partners."),
]


def test_matches_close_paraphrase():
    match = find_best_match("Can we visit the site on Sunday?", FAQS)
    assert match is not None
    assert match.faq_id == "FAQ002"


def test_no_match_for_unrelated_message():
    match = find_best_match("What amenities are included in the clubhouse?", FAQS)
    assert match is None


def test_empty_message_has_no_match():
    assert find_best_match("", FAQS) is None


def test_picks_highest_scoring_faq_when_multiple_overlap():
    match = find_best_match("Can you help arrange a home loan for me?", FAQS)
    assert match.faq_id == "FAQ003"
