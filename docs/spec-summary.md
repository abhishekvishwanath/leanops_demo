# Source spec summary — mumbai_real_estate_ai_demo_system.pdf

Transcribed from the original PDF provided at project kickoff (not committed as
a binary; this is the text content used to drive implementation decisions).

## 1. System outcome
Any lead from Meta ads, website forms, WhatsApp, or an incoming call is
normalized into one CRM record. Subject to consent and calling policy, the AI
attempts contact within 60 seconds, identifies the preferred language,
qualifies the buyer, matches suitable ERP inventory, sends an approved
WhatsApp media package, books a slot, notifies the salesperson, and continues
a controlled follow-up sequence.

## 2. Single end-to-end workflow
1. **Capture** — normalize phone/source/campaign/consent/timestamp → Lead record + immutable event
2. **Deduplicate** — match phone/email/device/source; detect duplicate/broker claim → New/merge/review queue
3. **Qualify** — extract language, locality, BHK, carpet area, budget, timeline, purpose, loan, parking, visit intent → structured fields + confidence
4. **Match** — filter fresh ERP inventory by availability/BHK/budget/area/locality, rank → approved property matches
5. **Contact** — AI disclosure, language choice, qualification, approved FAQ answers, human-transfer option, within 60s if permitted → call transcript, recording metadata, disposition
6. **Send** — approved multilingual project card/brochure/floor plan/images/video/map/disclaimer on WhatsApp → message log
7. **Escalate** — classify expertise-required questions/risk, create human task with priority/SLA/owner → escalation ticket
8. **Schedule** — offer only fresh available slots, recheck before booking, confirm + remind → appointment + calendar event
9. **Follow up** — no-answer: WhatsApp + retry; no-appointment: day 3/7/10; stop on reply/opt-out/booking/handoff/dead → scheduled jobs + opt-out enforcement
10. **Measure** — call quality, funnel conversion, source ROI, salesperson performance, inventory freshness, failures → dashboard + daily report

## 3. Dealer dashboard (control centre)
Every table editable, every change audited; AI reads only active+fresh records.

| Area | Sees | Can change |
|---|---|---|
| Executive funnel | New/contacted/qualified/appointments/attended/no-shows/bookings/dead, SLA | Filters (date/project/source/salesperson/language/status) |
| Live lead queue | Profile, source, score, dup flags, broker ownership, transcript, matches, next action | Assign/reassign, merge, disqualify, pause automation, edit, notes |
| ERP inventory | Projects/units/BHK/area/price/availability/possession/parking/media/freshness | Create/update/archive, price/availability approval, media upload |
| Salesperson board | Territory/languages/load/tasks/response time/conversion | Activate/deactivate, assign projects, capacity/routing |
| Slots and bookings | Available/held/booked/cancelled/completed/no-show | Create/block/reschedule/cancel, assign advisor, capacity |
| Follow-up centre | Due today/overdue/no-answer/nurture/opt-out/dead | Change next action, pause/resume/stop, edit templates |
| Escalation centre | Urgency/reason/expert type/owner/SLA/status/resolution | Assign expert, set priority, resolve/reopen, document answer |
| Quality and operations | Call score, hallucination flags, failed runs, webhook health, usage, provider errors | Review call, correct classification, approve script/template changes |

## 4. Duplicate and broker-lead handling
- Hard match: exact normalized phone. Soft matches: email, WhatsApp ID,
  name+last-4-digits, recent source/project combo.
- Never silently delete; preserve all source events; create a canonical lead.
- Auto-merge exact matches; uncertain matches → review queue; keep source
  attribution; retain consent history; assign one owner; notify broker + sales
  on ownership conflicts.
- Broker fields: `lead_type, broker_id, broker_name, source_partner,
  ownership_start, ownership_expiry, commission_category, claim_status,
  duplicate_of, canonical_lead_id`.

## 5. Human escalation classification
| Class | Examples | Action / SLA |
|---|---|---|
| E0 — routine | Project, BHK, carpet area, amenities, approved brochure | AI answers from fresh ERP/FAQ |
| E1 — sales | Negotiation, discount, final price, reservation, alternative project | Salesperson task; callback ≤15 min |
| E2 — inventory | Specific unit/floor/view, live availability, payment plan | Inventory/sales manager verification ≤10 min |
| E3 — finance | Loan eligibility, EMI, sanction, tax/statutory cost | Finance partner/senior advisor; same business day |
| E4 — legal/compliance | Title, RERA interpretation, agreement, dispute, possession claim | Legal/compliance expert; do not answer substantively |
| E5 — complaint/safety | Incorrect claim, harassment, refund, threat, urgent complaint | Immediate human takeover; supervisor alert |

## 6. Fresh data and edit controls
ERP/CRM/slots must carry `last_updated_at, updated_by, version, status,
approved_for_ai`. AI may read only active+approved records. Price/availability
/possession/slot changes invalidate cached answers immediately. Recommended:
bulk Excel import, row-level editing, archive-not-delete, change history,
approval workflow for prices/legal content, stale-data alerts, duplicate
prevention, mandatory reason for manual overrides, "sync now" action.

## 7. Multilingual message templates
Initial acknowledgement, no-answer, property match, appointment confirmation,
final follow-up — each has an English version and Hindi/Marathi handling notes
(approved native templates with variables; never translate prices/legal text
dynamically; include opt-out mechanism; preserve exact project/address
variables).

## 8. WhatsApp media package
Per project: project card, approved description, price sheet, unit
availability extract, brochure PDF, floor plans, unit layout, amenity images,
location map, site-visit instructions, possession statement, payment-plan
document, RERA verification link, disclaimer, last-updated timestamp.
Media metadata: `media_id, project_id, type, language, URL, version,
approval_status, valid_from, valid_until, checksum`. Send only after
permission, only from approved/current records.

## 9. Call-quality evaluation
Disclosure, Language, Qualification, Accuracy (no invented price/availability/
legal/loan claims), Conversation, Escalation, CRM (correct fields saved),
Booking (only fresh slots offered), Compliance (opt-out honoured, recording/
outbound policy followed).

## 10. Recommended technical architecture
Frontend: Next.js/React dashboard. Backend: FastAPI. Database: Supabase
Postgres with tenant_id + row-level security. Jobs: Redis/Celery or
Trigger.dev. Integrations: n8n for initial webhooks, Meta/WhatsApp Business
API, telephony/voice provider, Google Calendar, email/CRM APIs. Storage:
Supabase Storage or S3. Monitoring: Sentry + structured event logs. Analytics:
SQL views + Metabase or dashboard charts.

Core event types: `lead.created, lead.merged, duplicate.flagged,
lead.qualified, property.matched, call.started, call.completed,
escalation.created, appointment.booked, followup.due, optout.received,
inventory.updated, slot.updated, quality.reviewed`.

## 11. Final demo sequence
One successful lead Meta form → booked site visit; one duplicate lead merged
with broker ownership preserved; one no-answer lead entering 3/7/10 sequence;
one stale inventory record blocked from AI answers; one negotiation/legal
question escalated to human; one call-quality review shown on dashboard.

## 12. Dummy files included (original filenames in spec; provided to us as .csv)
`mumbai_property_erp_demo`, `mumbai_crm_leads_demo`,
`mumbai_crm_salespeople_demo`, `mumbai_crm_appointment_slots_demo`,
`mumbai_property_faq_approved_demo`, `mumbai_lead_automation_workflow_demo`.

**Production warning:** replace every dummy project/RERA/price/image/contact/
slot/FAQ record before live deployment. Apply consent, WhatsApp Business,
telecom, privacy, recording, and real-estate compliance requirements with the
client.
