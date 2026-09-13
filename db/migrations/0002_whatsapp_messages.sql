-- WhatsApp message log. Structured the way a real Twilio integration would
-- need it (provider + provider_message_id + status) so swapping the mock
-- provider for Twilio in Phase 6 is a data-shape no-op.

create table whatsapp_messages (
    message_id text primary key,
    tenant_id uuid not null references tenants(tenant_id),
    lead_id text references leads(lead_id),
    salesperson_id text references salespeople(salesperson_id),
    to_phone text not null,
    direction text not null default 'outbound',
    template_name text not null,
    language text not null,
    body text not null,
    media_urls text[] not null default '{}',
    status text not null default 'queued',       -- queued/sent/delivered/failed (mocked until Phase 6)
    provider text not null default 'mock',        -- 'mock' now, 'twilio' once connected
    provider_message_id text,
    created_at timestamptz not null default now()
);

create index idx_whatsapp_messages_lead on whatsapp_messages(lead_id);
create index idx_whatsapp_messages_salesperson on whatsapp_messages(salesperson_id);
