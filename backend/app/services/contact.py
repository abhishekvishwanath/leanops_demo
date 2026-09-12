"""
WF004/WF005 — outbound contact. Real telephony/WhatsApp providers are wired
in Phase 6 once credentials are available. Until then this stub returns what
the pipeline *would* have done, so the rest of the system (events, CRM
fields, dashboard) can be built and demoed against a stable interface.
"""
from typing import Optional


def mock_contact(*, consent: bool, language: Optional[str]) -> dict:
    if not consent:
        return {
            "channel": "none",
            "status": "skipped_no_consent",
            "note": "Consent not granted; no outbound call or WhatsApp message sent.",
        }
    return {
        "channel": "voice_call",
        "status": "queued_mock",
        "note": (
            "Real telephony/WhatsApp integration pending Phase 6 credentials. "
            f"Would disclose AI, confirm language ({language or 'unknown'}), and qualify."
        ),
    }
