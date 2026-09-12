# leanops_demo — XYZ Properties Mumbai AI Lead Conversion Demo

## What this is
A demo of an AI-driven real estate lead-to-site-visit pipeline for XYZ Properties
(Mumbai / Navi Mumbai / Thane). All project names, prices, RERA numbers, contacts,
and images in the seed data are dummy/illustrative — see `docs/spec-summary.md`
for the full source spec (originally `mumbai_real_estate_ai_demo_system.pdf`).

## Architecture (decided)
- Frontend: Next.js/React dealer dashboard
- Backend: FastAPI implementing the 10-stage pipeline (capture → dedupe → qualify
  → match → contact → send → escalate → schedule → follow-up → measure) as a
  state machine driven by `data/raw/mumbai_lead_automation_workflow_demo.csv`
- Database: Postgres (Supabase), tenant_id + row-level security
- Jobs: Redis/Celery for follow-up scheduling (day 3/7/10 sequences)
- Integrations (stubbed until credentials are provided, then wired in their own
  phase): WhatsApp Business API, telephony/voice provider, Google Calendar
- Storage: Supabase Storage / S3 for media package assets
- Monitoring: Sentry + structured event logs

Live credentials for WhatsApp, voice, telephony, and deployment are requested
only when that integration phase is actually reached — not before.

## Data
Raw seed CSVs live in `data/raw/`:
- `mumbai_property_erp_demo.csv` — ERP inventory, 1 row per project×BHK variant
- `mumbai_crm_leads_demo.csv` — 10 demo leads
- `mumbai_crm_salespeople_demo.csv` — 3 salespeople, territory/language/project ownership
- `mumbai_crm_appointment_slots_demo.csv` — bookable site-visit slots
- `mumbai_property_faq_approved_demo.csv` — approved FAQ answers (E0 tier)
- `mumbai_lead_automation_workflow_demo.csv` — the 12 workflow rules (WF001–WF012)

### Known gaps in the raw data (to be patched during Phase 1 seeding — user
confirmed "synthesize fixes" over "keep as-is")
- No slots exist at all for PRJ001, PRJ006, PRJ008, PRJ010, even though
  salespeople own them and leads (LD0005, LD0006, LD0009, LD0010) want them.
- LD0006 prefers Marathi but PRJ001 is solely owned by SP001 (English/Hindi only).
- LD0009 prefers Kannada; no salesperson speaks Kannada.
- No duplicate/broker-lead example exists, despite the broker schema in the
  spec (lead_type, broker_id, ownership_start/expiry, claim_status,
  canonical_lead_id, duplicate_of) and the demo requirement to show one
  duplicate merge with broker ownership preserved.
- No escalation ticket, call transcript, or call-quality review sample data
  (spec defines E0–E5 escalation classes and a call-quality rubric).
- No freshness/audit columns (`last_updated_at`, `updated_by`, `version`,
  `approved_for_ai`) on ERP/CRM/slots/FAQ — needed to demo "stale record
  blocked from AI".

Phase 1 will add synthetic rows/columns to close these gaps so every scenario
in the spec's final demo sequence has real data behind it, while keeping the
original CSVs in `data/raw/` untouched as the source of truth for what was
actually provided.

## Build phases
0. Analysis (done)
1. DB schema + seed data (normalize CSVs, patch gaps above) (done)
2. Backend pipeline engine: capture → dedupe → qualify → match → assign (mocked AI/contact) (done)
3. Scheduling (slots/booking/freshness) + follow-up sequencing (done)
4. Escalation classification (E0–E5) + dashboard escalation centre (done)
5. Dealer dashboard (Next.js) wired to backend (done)
6. Real integrations: WhatsApp Business API, voice/telephony, Google Calendar
7. Deployment

Backend so far lives entirely in `backend/app/`: `services/` holds pure,
DB-free business logic (phone, dedupe, qualify, matching, assignment,
contact, scheduling, followup, escalation, faq, metrics), `repositories.py`
is the only module that touches SQLAlchemy, `pipeline.py`/`booking.py`/
`followups.py`/`escalation_service.py` orchestrate. Escalation classification
is a keyword-based mock (E0 = FAQ match first, E1-E5 = risk keywords,
unclassified defaults to E1 rather than being dropped) — see the "Known
limitation" note in `escalation_service.py` about FAQ-match-first ordering
before changing it. See `backend/README.md` for the endpoint list and how
each phase was verified.

Frontend lives in `frontend/` — Next.js 16 (App Router), client-rendered
pages, Tailwind. One page per spec-section-3 dashboard area, all calling the
backend directly (CORS open for local dev). See `frontend/README.md` for the
route/endpoint map and the Next 16 `params`-is-now-a-Promise gotcha.
