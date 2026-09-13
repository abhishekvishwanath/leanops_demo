from app.services import whatsapp_templates as wt


def test_initial_acknowledgement_includes_name_and_phone():
    msg = wt.initial_acknowledgement(to_phone="+919810001001", name="Rohan Mehta")
    assert msg.to_phone == "+919810001001"
    assert "Rohan Mehta" in msg.body
    assert msg.template_name == "initial_acknowledgement"


def test_no_answer_followup():
    msg = wt.no_answer_followup(to_phone="+919810001001", name="Rohan")
    assert "Rohan" in msg.body
    assert msg.template_name == "no_answer"


def test_property_match_formats_price_and_carries_media():
    msg = wt.property_match(
        to_phone="+919810001001", name="Rohan", project_name="Metroview Enclave",
        bhk="2BHK", base_price_inr=12_900_000, media_urls=["https://example.com/card.jpg"],
    )
    assert "₹129.0L" in msg.body
    assert "Metroview Enclave" in msg.body
    assert msg.media_urls == ["https://example.com/card.jpg"]


def test_appointment_confirmation_includes_all_variables():
    msg = wt.appointment_confirmation(
        to_phone="+919810001001", name="Rohan", date="2026-09-13", time="11:00", advisor_name="Amit Verma"
    )
    assert "2026-09-13" in msg.body
    assert "11:00" in msg.body
    assert "Amit Verma" in msg.body


def test_sequence_reminder_day_is_in_template_name():
    msg3 = wt.sequence_reminder(to_phone="+919810001001", name="Rohan", day=3)
    msg7 = wt.sequence_reminder(to_phone="+919810001001", name="Rohan", day=7)
    assert msg3.template_name == "sequence_reminder_day3"
    assert msg7.template_name == "sequence_reminder_day7"


def test_final_followup_mentions_stopping_reminders():
    msg = wt.final_followup(to_phone="+919810001001", name="Rohan")
    assert "stop reminders" in msg.body.lower()


def test_salesperson_notification_includes_lead_and_project_details():
    msg = wt.salesperson_slot_notification(
        to_phone="+919820000101", salesperson_name="Amit Verma", lead_name="Rohan Mehta",
        lead_phone="+919810001001", project_name="Metroview Enclave", date="2026-09-13", time="11:00",
    )
    assert "Rohan Mehta" in msg.body
    assert "+919810001001" in msg.body
    assert "Metroview Enclave" in msg.body
    assert msg.to_phone == "+919820000101"
