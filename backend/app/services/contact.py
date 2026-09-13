"""
WF004/WF005 — outbound voice call attempt. Retell AI is wired in once its
credentials are available; until then this stub returns what the call
*would* have done, so the rest of the system (events, CRM fields, dashboard)
can be built and demoed against a stable interface.

WhatsApp messaging is a separate, already-production-shaped layer — see
app/whatsapp_service.py and app/services/whatsapp_templates.py — since only
the WhatsApp/Meta business account is being mocked pending Twilio
credentials, while voice/Retell setup hasn't started yet.
"""
from typing import Optional


def mock_contact(*, consent: bool, language: Optional[str]) -> dict:
    if not consent:
        return {
            "channel": "none",
            "status": "skipped_no_consent",
            "note": "Consent not granted; no outbound call attempted.",
        }
    return {
        "channel": "voice_call",
        "status": "queued_mock",
        "note": (
            "Real Retell telephony integration pending credentials. "
            f"Would disclose AI, confirm language ({language or 'unknown'}), and qualify."
        ),
    }
