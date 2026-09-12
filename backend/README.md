# Backend — lead pipeline API

FastAPI service implementing WF001-WF006 (capture, dedupe, qualify, match,
assign) against the schema in `db/migrations/0001_init.sql`. Contact
(WF004/WF005) is mocked until WhatsApp/telephony credentials are wired up in
a later phase — see `app/services/contact.py`.

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

- `POST /leads` — capture a lead and run the full pipeline
- `GET /leads` — list leads (`?status=`, `?project_id=`)
- `GET /leads/{lead_id}` — lead detail + its event log
- `GET /health`

## Test

```bash
pytest
```

All 30+ tests are pure unit tests against `app/services/*` and `app/domain.py`
— no database required. They run against in-memory dataclasses, not the ORM.

Integration/end-to-end verification (migration + seed + live API calls) was
done manually against a throwaway local Postgres container rather than
automated, to avoid adding Docker-in-CI complexity for a demo of this size.
See the Phase 2 commit for the scenarios exercised (clean lead, hard-match
duplicate, broker-conflict duplicate, soft-match review queue, language-gap
fallback assignment, stale-inventory exclusion).

## Architecture note

`app/services/*` are pure functions operating on the dataclasses in
`app/domain.py` — no SQLAlchemy imports. `app/repositories.py` is the only
place that talks to the database and converts rows to/from those
dataclasses. `app/pipeline.py` wires services + repository calls together
per request. Keep new business logic in `services/`, not in `pipeline.py` or
`main.py`, so it stays unit-testable without a database.
