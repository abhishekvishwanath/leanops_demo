# Synthetic seed additions

Everything below was fabricated by the seed script (`seed.py`) to close the
data gaps identified in Phase 0 (see `CLAUDE.md`), so every scenario in the
spec's final demo sequence (§11) has real rows behind it. The original
`data/raw/*.csv` files are never modified — these additions exist only in the
generated/loaded seed data (`data/seed/*.csv` or the database).

## 1. Missing slots (PRJ001, PRJ006, PRJ008, PRJ010)
Added 3 slots each (11:00 / 14:00 / 16:30) with their owning salesperson:
- PRJ001 → SP001, 2026-09-15 (`SL0071100/1400/1630`)
- PRJ006 → SP003, 2026-09-15 (`SL0081100/1400/1630`)
- PRJ008 → SP002, 2026-09-15 (`SL0091100/1400/1630`)
- PRJ010 → SP001, 2026-09-16, different day from PRJ001 to avoid double-booking
  SP001 (`SL0101100/1400/1630`)

## 2. Language coverage gap (Marathi/Kannada)
Added a 4th, cross-territory salesperson rather than rewriting SP001's real
profile:
- `SP004` Divya Rao — English, Hindi, Marathi, Kannada, Telugu — role
  `floating_specialist`, no exclusive project ownership.
- `LD0006` (Marathi, interested in PRJ001, SP001-owned) → `assigned_salesperson_id`
  set to SP004; SP001 stays the inventory owner of record for PRJ001.
- `LD0009` (Kannada, interested in PRJ010, SP001-owned) → left unassigned
  (status is still `New`) but gets a `lead.routing_recommended` event pointing
  to SP004, so the recommendation is visible without contradicting its status.

## 3. Duplicate / broker lead
Added `LD0011`, a duplicate of `LD0001`:
- Same phone (+919810001001), submitted later the same day via a different
  channel (Website Form vs. Meta Lead Ads) and claimed by a broker.
- `duplicate_of` / `canonical_lead_id` → `LD0001` (hard match on phone → auto-merge
  per spec §4), but `claim_status = 'Under Review'` because a broker ownership
  claim conflicts with the existing direct-source lead.
- `lead_events` rows: `duplicate.flagged` on LD0011, `lead.merged` on LD0001
  noting the pending broker claim.

## 4. Escalation tickets (spec §5, classes E0-E5)
Three tickets, spanning three classes, each tied to an existing lead:
- **E1 (sales)** — `LD0003`: requested a discount / unit reservation. Routed
  to the project-owning salesperson, 15-min callback SLA.
- **E2 (inventory)** — `LD0010`: asked for the current price of PRJ008 1BHK,
  which is the same unit marked stale/not-approved-for-AI below. Routed to an
  inventory manager, 10-min SLA.
- **E4 (legal/compliance)** — `LD0004`: asked whether the developer pays
  compensation for delayed possession. Routed to a legal/compliance expert;
  AI must not answer substantively. Same-business-day SLA.

## 5. Call transcript + quality review (spec §9)
Two calls, to show both a clean pass and a flagged failure:
- `LD0001`: full qualification call, disposition "Qualified — site visit
  requested," quality review passes every rubric dimension.
- `LD0005`: call where the agent quoted an unapproved rental-yield projection
  not present in ERP/FAQ data → `accuracy_pass = false`,
  `hallucination_flag = true`, flagged for human follow-up.

## 6. Stale inventory record (spec §11 demo item)
`PRJ008` / 1BHK unit (Skyline 45) marked `approved_for_ai = false`, with a
`stale_note` explaining pricing is under revision. This is the unit LD0010
asked about in the E2 escalation above — the AI must decline to quote it and
the ticket exists because of exactly that block.

## 7. Slot status variety (spec §3 lists 6 slot states; raw data only had "Available")
- `LD0004` → one PRJ005 slot set to `Held` (offered, awaiting confirmation)
- `LD0008` → one PRJ009 slot set to `Booked`
- `LD0005` → one of the new PRJ006 slots set to `Cancelled` (6–12 month
  timeline, deferred)
`Completed` / `No-show` are left for Phase 3 once visit-completion logic exists.

## 8. Media assets (spec §8)
One `project_card` media row per project (English), reusing the ERP
`image_url` already present, `approval_status = 'approved'`. This is a
placeholder set — the real multi-asset-per-project package (brochure, floor
plan, price sheet, etc.) is built in the WhatsApp integration phase.
