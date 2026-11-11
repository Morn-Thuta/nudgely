-- Nudgely v1 schema (docs/V1_ARCHITECTURE.md).
-- Run once in the Supabase SQL editor (or via the Supabase CLI) on a new project.
-- The backend writes with the service_role key (bypasses RLS).
-- The dashboard reads with the publishable/anon key, signed in (RLS: authenticated users can read).
-- Phone numbers are never stored here: customers are identified by their Nudgely id (WA001, WEB001, C001).

create table if not exists public.customers (
  id           text primary key,
  channel      text not null check (channel in ('whatsapp', 'web', 'demo')),
  name         text,
  label        text not null default 'New',
  uplift       real,
  p_no_msg     real,
  handover     boolean not null default false,
  opted_out    boolean not null default false,
  created_at   timestamptz not null default now(),
  last_seen_at timestamptz not null default now()
);

create table if not exists public.messages (
  id           bigint generated always as identity primary key,
  customer_id  text not null references public.customers(id) on delete cascade,
  sender       text not null check (sender in ('customer', 'store')),
  text         text not null,
  handover     boolean not null default false,
  created_at   timestamptz not null default now()
);
create index if not exists messages_customer_created on public.messages (customer_id, created_at);

create table if not exists public.tags (
  id           bigint generated always as identity primary key,
  customer_id  text not null references public.customers(id) on delete cascade,
  type         text not null,
  value        text not null,
  evidence     text not null,
  created_at   timestamptz not null default now(),
  unique (customer_id, type, value)
);

-- Row level security: nobody reads anything unless signed in; only the backend (service_role) writes.
alter table public.customers enable row level security;
alter table public.messages  enable row level security;
alter table public.tags      enable row level security;

drop policy if exists "signed-in can read customers" on public.customers;
drop policy if exists "signed-in can read messages"  on public.messages;
drop policy if exists "signed-in can read tags"      on public.tags;
create policy "signed-in can read customers" on public.customers for select to authenticated using (true);
create policy "signed-in can read messages"  on public.messages  for select to authenticated using (true);
create policy "signed-in can read tags"      on public.tags      for select to authenticated using (true);

-- The owner can resolve a handover from the dashboard.
drop policy if exists "signed-in can resolve handovers" on public.customers;
create policy "signed-in can resolve handovers" on public.customers for update to authenticated
  using (true) with check (true);

-- Realtime: the live dashboard listens for new rows.
do $$
begin
  begin alter publication supabase_realtime add table public.customers; exception when duplicate_object then null; end;
  begin alter publication supabase_realtime add table public.messages;  exception when duplicate_object then null; end;
  begin alter publication supabase_realtime add table public.tags;      exception when duplicate_object then null; end;
end $$;
