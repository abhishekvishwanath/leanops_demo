"""
Dispatches a composed WhatsAppMessage (see app/services/whatsapp_templates.py):
persists it to whatsapp_messages, logs a lead_event when it's tied to a
lead, and calls the provider.

`_provider_send` is the ONLY function in this WhatsApp layer that changes
when real Twilio/Meta credentials arrive. Its return contract
(provider, provider_message_id, status) matches what Twilio's
`client.messages.create(...)` gives back, so replacing its body with a real
API call requires no changes anywhere else — not in the templates, not in
the callers that decide when to send, not in the schema.
"""
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app import repositories
from app.domain import WhatsAppMessage


def _provider_send(message: WhatsAppMessage) -> dict:
    """
    MOCK provider — pending Twilio/Meta WhatsApp Business credentials.
    Replace this body with:
        response = twilio_client.messages.create(
            from_=WHATSAPP_SENDER, to=f"whatsapp:{message.to_phone}",
            body=message.body, media_url=message.media_urls or None,
        )
        return {"provider": "twilio", "provider_message_id": response.sid, "status": response.status}
    """
    return {
        "provider": "mock",
        "provider_message_id": f"MOCK-{uuid.uuid4().hex[:12]}",
        "status": "queued",
    }


def send(
    db: Session,
    message: WhatsAppMessage,
    *,
    lead_id: Optional[str] = None,
    salesperson_id: Optional[str] = None,
) -> dict:
    result = _provider_send(message)
    message_id = f"WA-{uuid.uuid4().hex[:12]}"

    repositories.insert_whatsapp_message(
        db,
        message_id=message_id,
        lead_id=lead_id,
        salesperson_id=salesperson_id,
        to_phone=message.to_phone,
        template_name=message.template_name,
        language=message.language,
        body=message.body,
        media_urls=message.media_urls,
        status=result["status"],
        provider=result["provider"],
        provider_message_id=result["provider_message_id"],
    )

    if lead_id:
        repositories.insert_event(
            db, lead_id, "whatsapp.sent",
            {
                "message_id": message_id,
                "template": message.template_name,
                "to": message.to_phone,
                "status": result["status"],
            },
        )

    return {"message_id": message_id, **result}
