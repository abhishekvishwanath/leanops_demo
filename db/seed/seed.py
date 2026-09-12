#!/usr/bin/env python3
"""
Seed script for the XYZ Properties Mumbai lead-conversion demo.

Reads the raw CSVs in data/raw/, normalizes them into the schema defined in
db/migrations/0001_init.sql, and applies the synthetic patches documented in
db/seed/SYNTHETIC_ADDITIONS.md to close the data gaps found in Phase 0.

Usage:
    python db/seed/seed.py                 # dry run: writes data/seed/*.csv
    DATABASE_URL=postgres://... python db/seed/seed.py --load   # loads into Postgres/Supabase

The dry-run mode has no dependencies beyond the standard library, so the seed
data can be reviewed before any database connection exists. --load requires
psycopg2-binary (see db/seed/requirements.txt).
"""
import csv
import os
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "seed"

TENANT_ID = "00000000-0000-0000-0000-000000000001"


def read_csv(name):
    with open(RAW / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_projects_and_units():
    rows = read_csv("mumbai_property_erp_demo.csv")
    projects = {}
    units = []
    for r in rows:
        pid = r["project_id"]
        if pid not in projects:
            projects[pid] = {
                "project_id": pid,
                "tenant_id": TENANT_ID,
                "project_name": r["project_name"],
                "locality": r["locality"],
                "city": r["city"],
                "construction_status": r["status"],
                "rera_number": r["rera_number"],
                "possession": r["possession"],
                "total_floors": r["total_floors"],
                "amenity_count": r["amenity_count"],
                "view": r["view"],
                "parking_included": r["parking_included"] == "Yes",
                "last_updated_at": "2026-09-12T00:00:00Z",
                "updated_by": "seed_script",
                "version": 1,
                "approved_for_ai": True,
                "record_status": "active",
            }
        approved_for_ai = True
        stale_note = ""
        # Synthetic patch #6: stale/blocked unit
        if pid == "PRJ008" and r["bhk"] == "1BHK":
            approved_for_ai = False
            stale_note = (
                "Price under revision after cost-sheet audit; do not quote "
                "until finance re-approves."
            )
        units.append(
            {
                "project_id": pid,
                "bhk": r["bhk"],
                "carpet_sqft": r["carpet_sqft"],
                "base_price_inr": r["base_price_inr"],
                "image_url": r["image_url"],
                "last_updated_at": "2026-06-01T00:00:00Z" if not approved_for_ai else "2026-09-12T00:00:00Z",
                "updated_by": "seed_script",
                "version": 1,
                "approved_for_ai": approved_for_ai,
                "record_status": "active",
                "stale_note": stale_note,
            }
        )
    return list(projects.values()), units


def build_salespeople():
    rows = read_csv("mumbai_crm_salespeople_demo.csv")
    salespeople = []
    sp_projects = []
    for r in rows:
        salespeople.append(
            {
                "salesperson_id": r["salesperson_id"],
                "tenant_id": TENANT_ID,
                "name": r["name"],
                "languages": [l.strip() for l in r["languages"].split(",")],
                "territory": r["territory"],
                "phone": r["phone"],
                "email": r["email"],
                "active": r["active"] == "True",
                "role": "project_owner",
            }
        )
        for pid in r["projects"].split(","):
            sp_projects.append({"salesperson_id": r["salesperson_id"], "project_id": pid.strip()})

    # Synthetic patch #2: floating multilingual specialist
    salespeople.append(
        {
            "salesperson_id": "SP004",
            "tenant_id": TENANT_ID,
            "name": "Divya Rao",
            "languages": ["English", "Hindi", "Marathi", "Kannada", "Telugu"],
            "territory": "Cross-territory language specialist",
            "phone": "+919820000104",
            "email": "divya.rao@xyzproperties.demo",
            "active": True,
            "role": "floating_specialist",
        }
    )
    return salespeople, sp_projects


def build_leads():
    rows = read_csv("mumbai_crm_leads_demo.csv")
    leads = []
    events = []

    # project -> owning salesperson (single owner per project in this dataset)
    _, sp_projects = build_salespeople()
    owner_by_project = {row["project_id"]: row["salesperson_id"] for row in sp_projects}

    # which leads are actually assigned to their project owner
    assigned_to_owner = {"LD0001", "LD0003", "LD0004", "LD0007", "LD0008"}
    # Synthetic patch #2: language-driven override to the floating specialist
    assigned_to_sp004 = {"LD0006"}

    for r in rows:
        lead_id = r["lead_id"]
        assigned = None
        if lead_id in assigned_to_sp004:
            assigned = "SP004"
        elif lead_id in assigned_to_owner:
            assigned = owner_by_project.get(r["project_interest"])

        leads.append(
            {
                "lead_id": lead_id,
                "tenant_id": TENANT_ID,
                "name": r["name"],
                "phone": r["phone"],
                "email": r["email"],
                "source": r["source"],
                "project_interest": r["project_interest"],
                "bhk": r["bhk"],
                "budget_min_inr": r["budget_min_inr"],
                "budget_max_inr": r["budget_max_inr"],
                "preferred_localities": r["preferred_localities"],
                "language": r["language"],
                "timeline": r["timeline"],
                "last_intent": r["last_intent"],
                "lead_grade": r["lead_grade"],
                "lead_score": r["lead_score"],
                "created_at": r["created_at"],
                "status": r["status"],
                "assigned_salesperson_id": assigned,
                "lead_type": "direct",
                "broker_id": "",
                "broker_name": "",
                "source_partner": "",
                "ownership_start": "",
                "ownership_expiry": "",
                "commission_category": "",
                "claim_status": "",
                "duplicate_of": "",
                "canonical_lead_id": "",
            }
        )
        events.append(
            {
                "lead_id": lead_id,
                "event_type": "lead.created",
                "payload": f'{{"source": "{r["source"]}"}}',
                "created_at": r["created_at"],
            }
        )

    # Synthetic patch #2 (LD0009): recommend, don't reassign, since status is still "New"
    events.append(
        {
            "lead_id": "LD0009",
            "event_type": "lead.routing_recommended",
            "payload": (
                '{"recommended_salesperson_id": "SP004", "reason": '
                '"project owner SP001 does not speak Kannada"}'
            ),
            "created_at": "2026-09-12T10:56:30Z",
        }
    )

    # Synthetic patch #3: duplicate / broker lead
    leads.append(
        {
            "lead_id": "LD0011",
            "tenant_id": TENANT_ID,
            "name": "Rohan Mehta",
            "phone": "+919810001001",
            "email": "rohan.mehta@example.com",
            "source": "Website Form",
            "project_interest": "PRJ003",
            "bhk": "2BHK",
            "budget_min_inr": "6500000",
            "budget_max_inr": "14000000",
            "preferred_localities": "Ghatkopar / Vikhroli",
            "language": "English",
            "timeline": "0-3 months",
            "last_intent": "Submitted enquiry via broker-referred website form",
            "lead_grade": "A",
            "lead_score": "82",
            "created_at": "2026-09-12 11:40",
            "status": "Merged - Broker Claim Under Review",
            "assigned_salesperson_id": "",
            "lead_type": "broker_referred",
            "broker_id": "BRK001",
            "broker_name": "Reliable Realty Partners",
            "source_partner": "Reliable Realty Partners",
            "ownership_start": "2026-09-12",
            "ownership_expiry": "2026-10-12",
            "commission_category": "Standard",
            "claim_status": "Under Review",
            "duplicate_of": "LD0001",
            "canonical_lead_id": "LD0001",
        }
    )
    events.append(
        {
            "lead_id": "LD0011",
            "event_type": "duplicate.flagged",
            "payload": '{"match_type": "hard_match_phone", "canonical_lead_id": "LD0001"}',
            "created_at": "2026-09-12T11:40:05Z",
        }
    )
    events.append(
        {
            "lead_id": "LD0001",
            "event_type": "lead.merged",
            "payload": (
                '{"merged_lead_id": "LD0011", "reason": '
                '"broker ownership claim conflicts with existing direct-source lead", '
                '"claim_status": "Under Review"}'
            ),
            "created_at": "2026-09-12T11:40:10Z",
        }
    )

    return leads, events


def build_slots():
    rows = read_csv("mumbai_crm_appointment_slots_demo.csv")
    slots = []
    for r in rows:
        slots.append(
            {
                "slot_id": r["slot_id"],
                "tenant_id": TENANT_ID,
                "slot_date": r["date"],
                "slot_time": r["time"],
                "salesperson_id": r["salesperson_id"],
                "project_id": r["project_id"],
                "status": "Available",
                "lead_id": "",
                "last_updated_at": "2026-09-12T00:00:00Z",
                "updated_by": "seed_script",
                "version": 1,
                "approved_for_ai": True,
            }
        )

    # Synthetic patch #1: slots for projects with none
    new_slot_defs = [
        ("SL007", "PRJ001", "SP001", "2026-09-15"),
        ("SL008", "PRJ006", "SP003", "2026-09-15"),
        ("SL009", "PRJ008", "SP002", "2026-09-15"),
        ("SL010", "PRJ010", "SP001", "2026-09-16"),
    ]
    times = [("1100", "11:00"), ("1400", "14:00"), ("1630", "16:30")]
    for prefix, pid, sp, date in new_slot_defs:
        for suffix, t in times:
            slots.append(
                {
                    "slot_id": f"{prefix}{suffix}",
                    "tenant_id": TENANT_ID,
                    "slot_date": date,
                    "slot_time": t,
                    "salesperson_id": sp,
                    "project_id": pid,
                    "status": "Available",
                    "lead_id": "",
                    "last_updated_at": "2026-09-12T00:00:00Z",
                    "updated_by": "seed_script",
                    "version": 1,
                    "approved_for_ai": True,
                }
            )

    # Synthetic patch #7: slot status variety
    by_id = {s["slot_id"]: s for s in slots}
    by_id["SL0051100"]["status"] = "Held"
    by_id["SL0051100"]["lead_id"] = "LD0004"
    by_id["SL0031100"]["status"] = "Booked"
    by_id["SL0031100"]["lead_id"] = "LD0008"
    by_id["SL0081100"]["status"] = "Cancelled"
    by_id["SL0081100"]["lead_id"] = "LD0005"

    return slots


def build_faqs():
    rows = read_csv("mumbai_property_faq_approved_demo.csv")
    return [
        {
            "faq_id": r["faq_id"],
            "tenant_id": TENANT_ID,
            "category": r["category"],
            "question": r["question"],
            "approved_answer": r["approved_answer"],
            "last_updated_at": "2026-09-12T00:00:00Z",
            "updated_by": "seed_script",
            "version": 1,
            "approved_for_ai": True,
            "record_status": "active",
        }
        for r in rows
    ]


def build_workflow_rules():
    rows = read_csv("mumbai_lead_automation_workflow_demo.csv")
    return [
        {
            "workflow_id": r["workflow_id"],
            "trigger_event": r["trigger"],
            "channel_or_role": r["channel_or_role"],
            "action": r["action"],
            "output": r["output"],
            "sla_or_timing": r["sla_or_timing"],
        }
        for r in rows
    ]


def build_escalations():
    # Synthetic patch #4
    return [
        {
            "tenant_id": TENANT_ID,
            "lead_id": "LD0003",
            "escalation_class": "E1",
            "reason": "Requested a discount and asked to reserve the unit pending price approval.",
            "expert_type": "Salesperson",
            "owner": "SP001",
            "priority": "Medium",
            "sla_due_at": "2026-09-12T10:34:00Z",
            "status": "In Progress",
            "resolution": "",
            "created_at": "2026-09-12T10:19:30Z",
        },
        {
            "tenant_id": TENANT_ID,
            "lead_id": "LD0010",
            "escalation_class": "E2",
            "reason": "Asked for the current price of PRJ008 1BHK; the ERP record is marked stale and not approved for AI.",
            "expert_type": "Inventory Manager",
            "owner": "SP002",
            "priority": "High",
            "sla_due_at": "2026-09-12T11:08:00Z",
            "status": "Open",
            "resolution": "",
            "created_at": "2026-09-12T10:58:30Z",
        },
        {
            "tenant_id": TENANT_ID,
            "lead_id": "LD0004",
            "escalation_class": "E4",
            "reason": "Asked whether the developer pays compensation if possession is delayed beyond the RERA-committed date.",
            "expert_type": "Legal/Compliance",
            "owner": "",
            "priority": "High",
            "sla_due_at": "2026-09-13T18:00:00Z",
            "status": "Open",
            "resolution": "",
            "created_at": "2026-09-12T11:15:00Z",
        },
    ]


def build_calls_and_reviews():
    # Synthetic patch #5
    calls = [
        {
            "lead_id": "LD0001",
            "salesperson_id": "SP001",
            "channel": "voice",
            "language": "English",
            "transcript": (
                "AI: Hi, this is XYZ Properties' AI assistant calling about your enquiry "
                "for Metroview Enclave — I'm an AI, happy to hand you to a human anytime. "
                "Is English okay to continue in?\n"
                "Lead: Yes, English is fine.\n"
                "AI: Great — are you looking at a 1BHK or 2BHK, and what's your target budget?\n"
                "Lead: 2BHK, up to 1.4 crore.\n"
                "AI: The 2BHK at Metroview Enclave is priced at 1.29 crore for 665 sq ft carpet, "
                "west-facing, with parking included. Would you like to schedule a site visit?\n"
                "Lead: Yes, please.\n"
                "AI: I'll pass you to Amit, who owns this project, to confirm a slot."
            ),
            "recording_metadata": '{"duration_sec": 96, "recording_id": "REC-LD0001-01"}',
            "disposition": "Qualified - Site visit requested",
            "started_at": "2026-09-12T10:06:00Z",
            "ended_at": "2026-09-12T10:07:36Z",
        },
        {
            "lead_id": "LD0005",
            "salesperson_id": "SP003",
            "channel": "voice",
            "language": "English",
            "transcript": (
                "AI: Hi, this is XYZ Properties' AI assistant about Bayline Gardens — I'm an AI, "
                "happy to connect you to a human. Is this a good time?\n"
                "Lead: Sure, I'm looking at it as an investment.\n"
                "AI: Understood. Based on similar projects in Vashi, you could expect roughly "
                "8% annual rental yield.\n"
                "Lead: That sounds promising, can you send details?\n"
                "AI: I'll send the approved project card over WhatsApp."
            ),
            "recording_metadata": '{"duration_sec": 71, "recording_id": "REC-LD0005-01"}',
            "disposition": "Nurture - investment enquiry",
            "started_at": "2026-09-12T10:36:00Z",
            "ended_at": "2026-09-12T10:37:11Z",
        },
    ]
    reviews = [
        {
            "call_ref": "LD0001",
            "disclosure_pass": True,
            "language_pass": True,
            "qualification_pass": True,
            "accuracy_pass": True,
            "conversation_pass": True,
            "escalation_pass": True,
            "crm_pass": True,
            "booking_pass": True,
            "compliance_pass": True,
            "hallucination_flag": False,
            "reviewer": "QA Bot",
            "notes": "Meets all rubric dimensions; site visit correctly logged.",
        },
        {
            "call_ref": "LD0005",
            "disclosure_pass": True,
            "language_pass": True,
            "qualification_pass": True,
            "accuracy_pass": False,
            "conversation_pass": True,
            "escalation_pass": False,
            "crm_pass": True,
            "booking_pass": True,
            "compliance_pass": True,
            "hallucination_flag": True,
            "reviewer": "QA Bot",
            "notes": (
                "Agent quoted an unapproved 8% rental-yield projection not present in "
                "ERP/FAQ data. Should have been treated as an E3 finance question and "
                "escalated instead of answered. Flagged for retraining and human follow-up."
            ),
        },
    ]
    return calls, reviews


def build_media(projects):
    # Synthetic patch #8: one project_card per project, reusing ERP image_url
    rows = read_csv("mumbai_property_erp_demo.csv")
    first_image = {}
    for r in rows:
        first_image.setdefault(r["project_id"], r["image_url"])
    return [
        {
            "media_id": f"MEDIA-{pid}-CARD-EN",
            "project_id": pid,
            "type": "project_card",
            "language": "English",
            "url": first_image[pid],
            "version": 1,
            "approval_status": "approved",
            "valid_from": "2026-09-12T00:00:00Z",
            "valid_until": "",
            "checksum": "",
        }
        for pid in first_image
    ]


def write_csv(name, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    path = OUT / name
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {path.relative_to(ROOT)} ({len(rows)} rows)")


def assemble():
    projects, units = build_projects_and_units()
    salespeople, sp_projects = build_salespeople()
    leads, events = build_leads()
    slots = build_slots()
    faqs = build_faqs()
    workflow_rules = build_workflow_rules()
    escalations = build_escalations()
    calls, reviews = build_calls_and_reviews()
    media = build_media(projects)
    return {
        "projects": projects,
        "project_units": units,
        "salespeople": salespeople,
        "salesperson_projects": sp_projects,
        "leads": leads,
        "lead_events": events,
        "appointment_slots": slots,
        "faqs": faqs,
        "workflow_rules": workflow_rules,
        "escalation_tickets": escalations,
        "call_transcripts": calls,
        "quality_reviews": reviews,
        "media_assets": media,
    }


def dry_run(data):
    print("Dry run — writing processed/patched seed data to data/seed/*.csv\n")
    for name, rows in data.items():
        write_csv(f"{name}.csv", rows)
    print(
        "\nNo DATABASE_URL set / --load not passed, so nothing was written to a "
        "database. Review the files above, then re-run with --load once "
        "DATABASE_URL points at your Postgres/Supabase instance."
    )


def load_to_db(data, database_url):
    import psycopg2
    import psycopg2.extras

    conn = psycopg2.connect(database_url)
    try:
        with conn:
            with conn.cursor() as cur:
                # call_transcripts/quality_reviews need generated call_id, so
                # insert calls first and remember the id per lead reference.
                call_id_by_lead = {}

                def clean(v):
                    return None if v in ("", None) else v

                def insert(table, rows, columns):
                    if not rows:
                        return
                    cols = ", ".join(columns)
                    placeholders = ", ".join(["%s"] * len(columns))
                    sql = f"insert into {table} ({cols}) values ({placeholders})"
                    psycopg2.extras.execute_batch(
                        cur, sql, [[clean(r.get(c)) for c in columns] for r in rows]
                    )

                insert(
                    "projects",
                    data["projects"],
                    [
                        "project_id", "tenant_id", "project_name", "locality", "city",
                        "construction_status", "rera_number", "possession", "total_floors",
                        "amenity_count", "view", "parking_included", "last_updated_at",
                        "updated_by", "version", "approved_for_ai", "record_status",
                    ],
                )
                insert(
                    "project_units",
                    data["project_units"],
                    [
                        "project_id", "bhk", "carpet_sqft", "base_price_inr", "image_url",
                        "last_updated_at", "updated_by", "version", "approved_for_ai",
                        "record_status", "stale_note",
                    ],
                )
                for sp in data["salespeople"]:
                    cur.execute(
                        "insert into salespeople (salesperson_id, tenant_id, name, "
                        "languages, territory, phone, email, active, role) values "
                        "(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (
                            sp["salesperson_id"], sp["tenant_id"], sp["name"],
                            sp["languages"], sp["territory"], sp["phone"], sp["email"],
                            sp["active"], sp["role"],
                        ),
                    )
                insert(
                    "salesperson_projects", data["salesperson_projects"],
                    ["salesperson_id", "project_id"],
                )
                insert(
                    "leads", data["leads"],
                    [
                        "lead_id", "tenant_id", "name", "phone", "email", "source",
                        "project_interest", "bhk", "budget_min_inr", "budget_max_inr",
                        "preferred_localities", "language", "timeline", "last_intent",
                        "lead_grade", "lead_score", "created_at", "status",
                        "assigned_salesperson_id", "lead_type", "broker_id", "broker_name",
                        "source_partner", "ownership_start", "ownership_expiry",
                        "commission_category", "claim_status", "duplicate_of",
                        "canonical_lead_id",
                    ],
                )
                insert(
                    "lead_events", data["lead_events"],
                    ["lead_id", "event_type", "payload", "created_at"],
                )
                insert(
                    "appointment_slots", data["appointment_slots"],
                    [
                        "slot_id", "tenant_id", "slot_date", "slot_time", "salesperson_id",
                        "project_id", "status", "lead_id", "last_updated_at", "updated_by",
                        "version", "approved_for_ai",
                    ],
                )
                insert(
                    "faqs", data["faqs"],
                    [
                        "faq_id", "tenant_id", "category", "question", "approved_answer",
                        "last_updated_at", "updated_by", "version", "approved_for_ai",
                        "record_status",
                    ],
                )
                insert(
                    "workflow_rules", data["workflow_rules"],
                    ["workflow_id", "trigger_event", "channel_or_role", "action", "output", "sla_or_timing"],
                )
                insert(
                    "escalation_tickets", data["escalation_tickets"],
                    [
                        "tenant_id", "lead_id", "escalation_class", "reason", "expert_type",
                        "owner", "priority", "sla_due_at", "status", "resolution", "created_at",
                    ],
                )
                for call in data["call_transcripts"]:
                    cur.execute(
                        "insert into call_transcripts (tenant_id, lead_id, salesperson_id, "
                        "channel, language, transcript, recording_metadata, disposition, "
                        "started_at, ended_at) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                        "returning call_id",
                        (
                            TENANT_ID, call["lead_id"], call["salesperson_id"], call["channel"],
                            call["language"], call["transcript"], call["recording_metadata"],
                            call["disposition"], call["started_at"], call["ended_at"],
                        ),
                    )
                    call_id_by_lead[call["lead_id"]] = cur.fetchone()[0]
                for review in data["quality_reviews"]:
                    cur.execute(
                        "insert into quality_reviews (call_id, disclosure_pass, "
                        "language_pass, qualification_pass, accuracy_pass, "
                        "conversation_pass, escalation_pass, crm_pass, booking_pass, "
                        "compliance_pass, hallucination_flag, reviewer, notes) values "
                        "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (
                            call_id_by_lead[review["call_ref"]], review["disclosure_pass"],
                            review["language_pass"], review["qualification_pass"],
                            review["accuracy_pass"], review["conversation_pass"],
                            review["escalation_pass"], review["crm_pass"],
                            review["booking_pass"], review["compliance_pass"],
                            review["hallucination_flag"], review["reviewer"], review["notes"],
                        ),
                    )
                insert(
                    "media_assets", data["media_assets"],
                    [
                        "media_id", "project_id", "type", "language", "url", "version",
                        "approval_status", "valid_from", "valid_until", "checksum",
                    ],
                )
        print("Loaded seed data into", database_url.split("@")[-1])
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--load", action="store_true", help="Load into DATABASE_URL instead of a dry run")
    args = parser.parse_args()

    data = assemble()

    if args.load:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            print("ERROR: --load requires DATABASE_URL to be set.", file=sys.stderr)
            sys.exit(1)
        load_to_db(data, database_url)
    else:
        dry_run(data)


if __name__ == "__main__":
    main()
