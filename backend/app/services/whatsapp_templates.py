"""
WhatsApp message composition — spec section 7 (multilingual message
templates) and section 8 (media package). Pure functions only: building the
right message for the right moment is real production logic. Only the
actual network send is mocked (app/whatsapp_service.py's `_provider_send`),
pending Twilio/Meta credentials.

Hindi/Marathi bodies are intentionally not implemented: spec section 7
requires "approved native-language templates with variables... do not
translate prices or legal text dynamically" — that copy has to come from a
business/legal review, not from on-the-fly translation. Every function
below accepts a `language` and stamps it on the message for correct
routing/logging, but always renders the approved English copy until the
business supplies reviewed native-language templates to swap in.
"""
from app.domain import WhatsAppMessage


def _money(inr: int) -> str:
    return f"₹{inr / 100_000:.1f}L"


def initial_acknowledgement(to_phone: str, name: str, language: str = "English") -> WhatsAppMessage:
    body = (
        f"Hi {name}, thanks for enquiring with XYZ Properties. Our property "
        "assistant will help you find a suitable 1–3 BHK home."
    )
    return WhatsAppMessage(to_phone=to_phone, template_name="initial_acknowledgement", language=language, body=body)


def no_answer_followup(to_phone: str, name: str, language: str = "English") -> WhatsAppMessage:
    body = (
        f"Hi {name}, we tried reaching you about your property enquiry. "
        "Reply CALL for a callback or VISIT for site-visit options."
    )
    return WhatsAppMessage(to_phone=to_phone, template_name="no_answer", language=language, body=body)


def property_match(
    to_phone: str,
    name: str,
    project_name: str,
    bhk: str,
    base_price_inr: int,
    media_urls: list,
    language: str = "English",
) -> WhatsAppMessage:
    body = (
        f"Hi {name}, here is the approved information for {project_name} "
        f"({bhk}, {_money(base_price_inr)}) we discussed. Prices and "
        "availability are subject to confirmation."
    )
    return WhatsAppMessage(
        to_phone=to_phone, template_name="property_match", language=language, body=body, media_urls=media_urls
    )


def appointment_confirmation(
    to_phone: str, name: str, date: str, time: str, advisor_name: str, language: str = "English"
) -> WhatsAppMessage:
    body = f"Hi {name}, your site visit is confirmed for {date} at {time} with {advisor_name}."
    return WhatsAppMessage(to_phone=to_phone, template_name="appointment_confirmation", language=language, body=body)


def sequence_reminder(to_phone: str, name: str, day: int, language: str = "English") -> WhatsAppMessage:
    body = (
        f"Hi {name}, following up on your property enquiry — still interested? "
        "Reply VISIT to book a site visit or CALL for a callback."
    )
    return WhatsAppMessage(
        to_phone=to_phone, template_name=f"sequence_reminder_day{day}", language=language, body=body
    )


def final_followup(to_phone: str, name: str, language: str = "English") -> WhatsAppMessage:
    body = (
        f"Hi {name}, we will stop reminders unless you ask us to continue. "
        "Reply VISIT if your requirement is active."
    )
    return WhatsAppMessage(to_phone=to_phone, template_name="final_followup", language=language, body=body)


def salesperson_slot_notification(
    to_phone: str,
    salesperson_name: str,
    lead_name: str,
    lead_phone: str,
    project_name: str,
    date: str,
    time: str,
) -> WhatsAppMessage:
    """
    Internal staff notification, not a customer-facing template — this is
    what replaces a Google Calendar invite: the salesperson sees the booking
    on WhatsApp instead of their calendar. Since it's not sent to an
    end-customer, it isn't subject to Meta's approved-template rules the way
    the customer-facing templates above are.
    """
    body = (
        f"Hi {salesperson_name}, a new site visit is booked: {lead_name} "
        f"({lead_phone}) — {project_name} on {date} at {time}. View details "
        "in the dashboard."
    )
    return WhatsAppMessage(
        to_phone=to_phone, template_name="salesperson_slot_notification", language="English", body=body
    )
