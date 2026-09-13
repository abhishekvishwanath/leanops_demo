# Backend — lead pipeline API

FastAPI service implementing WF001-WF010 plus escalation classification
(capture, dedupe, qualify, match, assign, schedule, follow up, escalate)
against the schema in `db/migrations/0001_init.sql` + `0002_whatsapp_messages.sql`.

- **Voice** (`app/services/contact.py`) is mocked pending Retell AI credentials.
- **WhatsApp** (`app/whatsapp_service.py` + `app/services/whatsapp_templates.py`)
  is fully production-shaped — every trigger point composes and logs a real
  message — with only the final network call mocked pending Twilio/Meta
  credentials. See `app/whatsapp_service.py`'s docstring for exactly what
  changes when those arrive.
- **Google Calendar was dropped entirely**, not deferred: `appointment_slots`
  is the calendar of record, and confirming a booking notifies the
  salesperson over WhatsApp instead of a calendar invite.
- Escalation classification (spec section 5) is a keyword-based mock
  standing in for a real LLM classifier — see `app/services/escalation.py`.

## Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL (and Supabase keys if used)
```

## Run

```bash
uvicorn app.main:app --reload
```

**Pipeline (Phase 2)**
- `POST /leads` — capture a lead and run the full pipeline
- `GET /leads` — list leads (`?status=`, `?project_id=`)
- `GET /leads/{lead_id}` — lead detail + its event log

**Scheduling (Phase 3, WF008)**
- `GET /projects/{project_id}/slots` — list slots (`?status=`, `?slot_date=`)
- `POST /slots/{slot_id}/hold` `{lead_id}` — offer a slot (Available -> Held)
- `POST /slots/{slot_id}/confirm` `{lead_id}` — book it (Held -> Booked; 409 if raced or expired)
- `POST /slots/{slot_id}/cancel` `{reason}` — cancel a held/booked slot

**Follow-up sequencing (Phase 3, WF009/WF010)**
- `GET /follow-ups/due` — what a scheduler would act on right now
- `POST /leads/{lead_id}/follow-up` `{day}` — send day 3/7/10 (or a manual override for demo purposes)
- `POST /leads/{lead_id}/contact-outcome` `{outcome, channel}` — logs a call disposition; `no_answer` fires the immediate WF009 WhatsApp + retry task
- `POST /leads/{lead_id}/opt-out` — stops the sequence
- `POST /leads/{lead_id}/reply` — stops the sequence

**Escalation classification (Phase 4, WF stage 7, spec section 5)**
- `POST /classify` `{message}` — stateless risk classification only, no DB writes (for tuning the keyword rules)
- `POST /leads/{lead_id}/questions` `{message}` — FAQ match first (E0, answers directly), else risk-classifies into E1-E5 and opens a ticket; E5 also pauses the lead's automation
- `GET /escalations` — list tickets (`?status=`, `?escalation_class=`, `?owner=`)
- `GET /escalations/{ticket_id}` — ticket detail
- `PATCH /escalations/{ticket_id}` `{owner?, priority?, status?, resolution?}` — dashboard escalation-centre actions

**WhatsApp messaging** — no dedicated endpoints; it fires automatically at
each trigger point and is visible in a lead's event timeline (`whatsapp.sent`
events) and in the `whatsapp_messages` table:
- Lead capture (consent given): `initial_acknowledgement`, then `property_match` if inventory matched
- No-answer contact outcome: `no_answer` + a retry-task event
- Day 3/7 follow-up: `sequence_reminder_dayN`; day 10: `final_followup`
- Slot confirmed: `appointment_confirmation` to the lead **and**
  `salesperson_slot_notification` to the salesperson (the Google Calendar replacement)

- `GET /health`

## Test

```bash
pytest
```

All 75 tests are pure unit tests against `app/services/*` and `app/domain.py`
— no database required. They run against in-memory dataclasses, not the ORM.

Integration/end-to-end verification (migration + seed + live API calls) was
done manually against a throwaway local Postgres container rather than
automated, to avoid adding Docker-in-CI complexity for a demo of this size.
Phase 2 covered: clean lead, hard-match duplicate, broker-conflict duplicate,
soft-match review queue, language-gap fallback assignment, stale-inventory
exclusion. Phase 3 covered: hold/confirm booking, a lost-race 409 on a
double-hold, lead-status transitions on booking and cancellation, the
day-3/7/10 sequence (including "already sent" and "stopped by reply"),
no-answer retry, opt-out, and a freshness-guard 409 on a past-dated slot.
Phase 4 covered: the Phase 1 seeded E1/E2/E4 tickets read back correctly, a
live E0 FAQ answer, a live E1/E3/E5 classification each (E5 correctly pauses
the lead and blocks further follow-ups), an unclassified message correctly
defaulting to E1 rather than being dropped, and a PATCH resolving a ticket.
The WhatsApp layer was verified by capturing a live lead (confirmed
`initial_acknowledgement` + `property_match` rows, correctly ordered despite
being inserted before the lead row itself commits — SQLAlchemy's flush
respects FK dependencies across the whole unit of work), booking a slot
(confirmed both the lead-facing and salesperson-facing messages, with the
salesperson's real phone/name pulled from the roster), a no-answer outcome,
and a manual day-3 send.

## Architecture note

`app/services/*` are pure functions operating on the dataclasses in
`app/domain.py` — no SQLAlchemy imports. `app/repositories.py` is the only
place that talks to the database and converts rows to/from those
dataclasses. `app/pipeline.py` wires services + repository calls together
per request. Keep new business logic in `services/`, not in `pipeline.py` or
`main.py`, so it stays unit-testable without a database.
