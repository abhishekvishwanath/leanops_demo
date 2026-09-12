from app.services.phone import last4, normalize_phone


def test_normalize_bare_10_digit():
    assert normalize_phone("9810001001") == "+919810001001"


def test_normalize_already_has_country_code():
    assert normalize_phone("+919810001001") == "+919810001001"


def test_normalize_with_punctuation():
    assert normalize_phone("+91 98100-01001") == "+919810001001"


def test_normalize_91_prefix_no_plus():
    assert normalize_phone("919810001001") == "+919810001001"


def test_last4():
    assert last4("+919810001001") == "1001"


def test_last4_short_number():
    assert last4("12") == "12"
