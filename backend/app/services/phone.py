import re


def normalize_phone(raw: str) -> str:
    """
    Normalize an Indian phone number to E.164-ish form: +91XXXXXXXXXX.

    Strips spaces/dashes/parens. A bare 10-digit number is assumed to be
    Indian and gets +91 prepended. Anything already carrying a country code
    (11+ digits, or an explicit '+') is left as +<digits>.
    """
    digits = re.sub(r"[^\d+]", "", raw or "")
    digits = digits.lstrip("+")
    if len(digits) == 10:
        return f"+91{digits}"
    if digits.startswith("91") and len(digits) == 12:
        return f"+{digits}"
    return f"+{digits}" if digits else ""


def last4(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    return digits[-4:] if len(digits) >= 4 else digits
