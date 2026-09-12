-- XYZ Properties Mumbai lead-conversion demo — initial schema
-- Targets Supabase Postgres. Single-tenant for the demo, but every table
-- carries tenant_id so row-level-security policies can be added later
-- without a reshape (per spec section 10).

create extension if not exists "pgcrypto";

create table tenants (
    tenant_id uuid primary key default gen_random_uuid(),
    name text not null,
    created_at timestamptz not null default now()
);

insert into tenants (tenant_id, name)
values ('00000000-0000-0000-0000-000000000001', 'XYZ Properties (Demo)');

-- ---------------------------------------------------------------------------
-- ERP inventory
-- ---------------------------------------------------------------------------

create table projects (
    project_id text primary key,
    tenant_id uuid not null references tenants(tenant_id),
    project_name text not null,
    locality text not null,
    city text not null,
    construction_status text not null,          -- Under Construction / Ready to Move
    rera_number text not null,
    possession text not null,                    -- e.g. "Dec-2028" or "Ready"
    total_floors int not null,
    amenity_count int not null,
    view text not null,
    parking_included boolean not null,
    last_updated_at timestamptz not null default now(),
    updated_by text not null default 'seed_script',
    version int not null default 1,
    approved_for_ai boolean not null default true,
    record_status text not null default 'active' -- active / archived
);

create table project_units (
    unit_id bigint generated always as identity primary key,
    project_id text not null references projects(project_id),
    bhk text not null,
    carpet_sqft int not null,
    base_price_inr bigint not null,
    image_url text,
    last_updated_at timestamptz not null default now(),
    updated_by text not null default 'seed_script',
    version int not null default 1,
    approved_for_ai boolean not null default true,
    record_status text not null default 'active',
    stale_note text,                              -- populated when approved_for_ai = false
    unique (project_id, bhk)
);

-- ---------------------------------------------------------------------------
-- Salespeople
-- ---------------------------------------------------------------------------

create table salespeople (
    salesperson_id text primary key,
    tenant_id uuid not null references tenants(tenant_id),
    name text not null,
    languages text[] not null,
    territory text not null,
    phone text not null,
    email text not null,
    active boolean not null default true,
    role text not null default 'project_owner'    -- project_owner / floating_specialist
);

create table salesperson_projects (
    salesperson_id text not null references salespeople(salesperson_id),
    project_id text not null references projects(project_id),
    primary key (salesperson_id, project_id)
);

-- ---------------------------------------------------------------------------
-- Leads (+ dedupe/broker fields per spec section 4)
-- ---------------------------------------------------------------------------

create table leads (
    lead_id text primary key,
    tenant_id uuid not null references tenants(tenant_id),
    name text not null,
    phone text not null,
    email text,
    source text not null,
    project_interest text references projects(project_id),
    bhk text,
    budget_min_inr bigint,
    budget_max_inr bigint,
    preferred_localities text,
    language text,
    timeline text,
    last_intent text,
    lead_grade text,
    lead_score int,
    created_at timestamptz not null,
    status text not null,
    assigned_salesperson_id text references salespeople(salesperson_id),

    -- broker / duplicate handling
    lead_type text not null default 'direct',      -- direct / broker_referred
    broker_id text,
    broker_name text,
    source_partner text,
    ownership_start timestamptz,
    ownership_expiry timestamptz,
    commission_category text,
    claim_status text,                             -- e.g. Under Review / Confirmed / Rejected
    duplicate_of text references leads(lead_id),
    canonical_lead_id text references leads(lead_id)
);

create table lead_events (
    event_id bigint generated always as identity primary key,
    lead_id text not null references leads(lead_id),
    event_type text not null,                      -- lead.created, lead.merged, duplicate.flagged, ...
    payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Appointment slots
-- ---------------------------------------------------------------------------

create table appointment_slots (
    slot_id text primary key,
    tenant_id uuid not null references tenants(tenant_id),
    slot_date date not null,
    slot_time time not null,
    salesperson_id text not null references salespeople(salesperson_id),
    project_id text not null references projects(project_id),
    status text not null default 'Available',      -- Available/Held/Booked/Cancelled/Completed/No-show
    lead_id text references leads(lead_id),
    last_updated_at timestamptz not null default now(),
    updated_by text not null default 'seed_script',
    version int not null default 1,
    approved_for_ai boolean not null default true
);

-- ---------------------------------------------------------------------------
-- FAQs (E0 tier answers)
-- ---------------------------------------------------------------------------

create table faqs (
    faq_id text primary key,
    tenant_id uuid not null references tenants(tenant_id),
    category text not null,
    question text not null,
    approved_answer text not null,
    last_updated_at timestamptz not null default now(),
    updated_by text not null default 'seed_script',
    version int not null default 1,
    approved_for_ai boolean not null default true,
    record_status text not null default 'active'
);

-- ---------------------------------------------------------------------------
-- Escalations (E0-E5 classification, spec section 5)
-- ---------------------------------------------------------------------------

create table escalation_tickets (
    ticket_id bigint generated always as identity primary key,
    tenant_id uuid not null references tenants(tenant_id),
    lead_id text not null references leads(lead_id),
    escalation_class text not null,                -- E0..E5
    reason text not null,
    expert_type text,
    owner text,
    priority text,
    sla_due_at timestamptz,
    status text not null default 'Open',           -- Open/In Progress/Resolved/Reopened
    resolution text,
    created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Call transcripts + quality reviews (spec section 9)
-- ---------------------------------------------------------------------------

create table call_transcripts (
    call_id bigint generated always as identity primary key,
    tenant_id uuid not null references tenants(tenant_id),
    lead_id text not null references leads(lead_id),
    salesperson_id text references salespeople(salesperson_id),
    channel text not null,                         -- voice / whatsapp
    language text,
    transcript text,
    recording_metadata jsonb default '{}'::jsonb,
    disposition text,
    started_at timestamptz,
    ended_at timestamptz
);

create table quality_reviews (
    review_id bigint generated always as identity primary key,
    call_id bigint not null references call_transcripts(call_id),
    disclosure_pass boolean not null,
    language_pass boolean not null,
    qualification_pass boolean not null,
    accuracy_pass boolean not null,
    conversation_pass boolean not null,
    escalation_pass boolean not null,
    crm_pass boolean not null,
    booking_pass boolean not null,
    compliance_pass boolean not null,
    hallucination_flag boolean not null default false,
    reviewer text not null,
    notes text,
    created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- WhatsApp media package metadata (spec section 8)
-- ---------------------------------------------------------------------------

create table media_assets (
    media_id text primary key,
    project_id text not null references projects(project_id),
    type text not null,                            -- project_card/brochure/floor_plan/...
    language text not null,
    url text not null,
    version int not null default 1,
    approval_status text not null default 'approved',
    valid_from timestamptz not null default now(),
    valid_until timestamptz,
    checksum text
);

-- ---------------------------------------------------------------------------
-- Workflow rules (reference copy of WF001-WF012, for dashboard visibility)
-- ---------------------------------------------------------------------------

create table workflow_rules (
    workflow_id text primary key,
    trigger_event text not null,
    channel_or_role text not null,
    action text not null,
    output text not null,
    sla_or_timing text not null
);

create index idx_leads_project_interest on leads(project_interest);
create index idx_leads_phone on leads(phone);
create index idx_slots_project_status on appointment_slots(project_id, status);
create index idx_slots_salesperson on appointment_slots(salesperson_id);
create index idx_escalation_lead on escalation_tickets(lead_id);
